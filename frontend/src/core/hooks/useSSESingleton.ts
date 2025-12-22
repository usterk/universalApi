import { useEffect, useState, useCallback } from 'react'
import { useAuthStore } from '@/core/stores/auth'
import { api } from '@/core/api/client'
import type { SSEEvent, TimelineJob } from './useSSE'

// Connection state enum
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DEGRADED = 'degraded',    // SSE OK but backend unhealthy
  ERROR = 'error'
}

// Global singleton EventSource connection
class SSEManager {
  private eventSource: EventSource | null = null
  private subscribers: Set<(event: SSEEvent) => void> = new Set()
  private reconnectTimeout: NodeJS.Timeout | null = null
  private disconnectTimeout: NodeJS.Timeout | null = null
  private currentToken: string | null = null
  private isConnecting = false
  private connectionCount = 0

  // State management
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED
  private connectionListeners: Set<(connected: boolean) => void> = new Set()
  private stateListeners: Set<(state: ConnectionState) => void> = new Set()

  // Keepalive monitoring
  private lastKeepaliveTime: number | null = null
  private keepaliveCheckInterval: NodeJS.Timeout | null = null

  // Health check monitoring
  private healthCheckInterval: NodeJS.Timeout | null = null

  // Reconnection tracking
  private reconnectAttempts = 0

  // State management methods
  private setConnectionState(state: ConnectionState) {
    if (this.connectionState !== state) {
      console.log(`[SSEManager] State: ${this.connectionState} -> ${state}`)
      this.connectionState = state

      // Notify boolean listeners (backward compat)
      const isConnected = state === ConnectionState.CONNECTED
      this.notifyConnectionChange(isConnected)

      // Notify state listeners
      this.notifyStateChange(state)
    }
  }

  getConnectionState(): ConnectionState {
    return this.connectionState
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts
  }

  connect(token: string) {
    // If already connected with same token, don't reconnect
    if (this.eventSource && this.currentToken === token) {
      console.log('[SSEManager] Already connected with same token')
      return
    }

    // Close existing connection if token changed
    if (this.currentToken !== token) {
      console.log('[SSEManager] Token changed, closing old connection')
      this.disconnect()
    }

    if (this.isConnecting) {
      console.log('[SSEManager] Connection already in progress')
      return
    }

    // CRITICAL FIX: Set CONNECTING state BEFORE creating EventSource
    this.setConnectionState(ConnectionState.CONNECTING)

    this.isConnecting = true
    this.currentToken = token
    this.connectionCount++
    const connId = this.connectionCount

    const url = `/api/v1/events/stream?token=${token}&types=job.started,job.progress,job.completed,job.failed`

    console.log(`[SSEManager #${connId}] Connecting to ${url}`)
    const eventSource = new EventSource(url)
    this.eventSource = eventSource

    eventSource.onopen = () => {
      this.isConnecting = false
      this.reconnectAttempts = 0  // Reset on success
      console.log(`[SSEManager #${connId}] Connected`)

      this.setConnectionState(ConnectionState.CONNECTED)
      this.startKeepaliveMonitoring()
      this.startHealthCheckMonitoring()
    }

    const handleEvent = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent
        this.subscribers.forEach((callback) => callback(data))
      } catch (error) {
        console.error('[SSEManager] Failed to parse event:', error)
      }
    }

    // Listen to all event types
    eventSource.onmessage = handleEvent
    ;['job.started', 'job.progress', 'job.completed', 'job.failed'].forEach((type) => {
      eventSource.addEventListener(type, handleEvent)
    })

    eventSource.addEventListener('keepalive', () => {
      console.log(`[SSEManager #${connId}] Keepalive received`)
      this.lastKeepaliveTime = Date.now()  // Update timestamp
    })

    eventSource.onerror = async (event) => {
      this.isConnecting = false
      console.error(`[SSEManager #${connId}] Connection error`, event)

      this.stopKeepaliveMonitoring()
      this.setConnectionState(ConnectionState.ERROR)

      // Try token refresh if closed
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken && eventSource.readyState === EventSource.CLOSED) {
        try {
          console.log('[SSEManager] Attempting token refresh')
          await api.me()
          const newToken = useAuthStore.getState().accessToken
          if (newToken) {
            this.scheduleReconnect(newToken)
            return
          }
        } catch (error) {
          console.error('[SSEManager] Token refresh failed:', error)
        }
      }

      // Auto-reconnect with smart strategy
      this.scheduleReconnect(token)
    }
  }

  // Keepalive monitoring
  private startKeepaliveMonitoring() {
    if (this.keepaliveCheckInterval) {
      clearInterval(this.keepaliveCheckInterval)
    }

    this.lastKeepaliveTime = Date.now()

    // Check every 10s
    this.keepaliveCheckInterval = setInterval(() => {
      const now = Date.now()
      const elapsed = now - (this.lastKeepaliveTime || now)

      // Backend sends keepalive every 15s, allow 25s tolerance
      if (elapsed > 25000) {
        console.warn(`[SSEManager] No keepalive for ${elapsed}ms, reconnecting`)
        this.handleStaleConnection()
      }
    }, 10000)
  }

  private handleStaleConnection() {
    this.stopKeepaliveMonitoring()
    const token = this.currentToken
    this.disconnect()
    if (token) {
      this.scheduleReconnect(token)
    }
  }

  private stopKeepaliveMonitoring() {
    if (this.keepaliveCheckInterval) {
      clearInterval(this.keepaliveCheckInterval)
      this.keepaliveCheckInterval = null
    }
    this.lastKeepaliveTime = null
  }

  // Health check monitoring
  private startHealthCheckMonitoring() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval)
    }

    this.healthCheckInterval = setInterval(async () => {
      try {
        const response = await fetch('/health', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!response.ok) {
          console.warn(`[SSEManager] Health check failed: ${response.status}`)
          if (this.connectionState === ConnectionState.CONNECTED) {
            this.setConnectionState(ConnectionState.DEGRADED)
          }
        } else {
          const data = await response.json()

          if (data.status === 'degraded') {
            console.warn('[SSEManager] Backend degraded:', data)
            if (this.connectionState === ConnectionState.CONNECTED) {
              this.setConnectionState(ConnectionState.DEGRADED)
            }
          } else if (data.status === 'healthy') {
            // Upgrade from degraded to connected
            if (this.connectionState === ConnectionState.DEGRADED) {
              this.setConnectionState(ConnectionState.CONNECTED)
            }
          }
        }
      } catch (error) {
        console.error('[SSEManager] Health check error:', error)
        if (this.connectionState === ConnectionState.CONNECTED) {
          this.setConnectionState(ConnectionState.DEGRADED)
        }
      }
    }, 30000)  // Every 30s
  }

  private stopHealthCheckMonitoring() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval)
      this.healthCheckInterval = null
    }
  }

  // Smart reconnection strategy
  private scheduleReconnect(token: string) {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }

    this.reconnectAttempts++

    // Aggressive retry strategy (no max limit):
    // 0-2min: every 10s (attempts 1-12)
    // 2-12min: every 30s (attempts 13-32)
    // 12min-1h12min: every 1min (attempts 33-92)
    // After: every 5min (attempts 93+)
    let delay: number

    if (this.reconnectAttempts <= 12) {
      delay = 10000  // 10s for first 2 minutes
    } else if (this.reconnectAttempts <= 32) {
      delay = 30000  // 30s for next 10 minutes
    } else if (this.reconnectAttempts <= 92) {
      delay = 60000  // 1min for next hour
    } else {
      delay = 300000  // 5min thereafter
    }

    console.log(`[SSEManager] Reconnect attempt ${this.reconnectAttempts} in ${delay}ms`)

    this.reconnectTimeout = setTimeout(() => {
      console.log(`[SSEManager] Auto-reconnecting (attempt ${this.reconnectAttempts})`)
      this.connect(token)
    }, delay)
  }

  disconnect() {
    console.log('[SSEManager] Disconnecting')

    // Stop all monitoring
    this.stopKeepaliveMonitoring()
    this.stopHealthCheckMonitoring()

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.disconnectTimeout) {
      clearTimeout(this.disconnectTimeout)
      this.disconnectTimeout = null
    }

    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }

    this.isConnecting = false
    this.currentToken = null
    this.setConnectionState(ConnectionState.DISCONNECTED)
  }

  subscribe(callback: (event: SSEEvent) => void): () => void {
    this.subscribers.add(callback)

    // Cancel any pending disconnect since we have a new subscriber
    if (this.disconnectTimeout) {
      console.log('[SSEManager] New subscriber, canceling pending disconnect')
      clearTimeout(this.disconnectTimeout)
      this.disconnectTimeout = null
    }

    return () => {
      this.subscribers.delete(callback)

      // If no more subscribers, schedule disconnect after delay
      // This handles React StrictMode remounting
      if (this.subscribers.size === 0) {
        console.log('[SSEManager] No more subscribers, will disconnect in 2s...')
        this.disconnectTimeout = setTimeout(() => {
          if (this.subscribers.size === 0) {
            console.log('[SSEManager] Still no subscribers, disconnecting')
            this.disconnect()
          }
        }, 2000)
      }
    }
  }

  onConnectionChange(callback: (connected: boolean) => void): () => void {
    this.connectionListeners.add(callback)

    // CRITICAL FIX: Use our state, not EventSource.readyState
    callback(this.connectionState === ConnectionState.CONNECTED)

    return () => {
      this.connectionListeners.delete(callback)
    }
  }

  private notifyConnectionChange(connected: boolean) {
    this.connectionListeners.forEach((callback) => callback(connected))
  }

  onStateChange(callback: (state: ConnectionState) => void): () => void {
    this.stateListeners.add(callback)
    callback(this.connectionState)  // Notify immediately
    return () => {
      this.stateListeners.delete(callback)
    }
  }

  private notifyStateChange(state: ConnectionState) {
    this.stateListeners.forEach(cb => cb(state))
  }

  isConnected(): boolean {
    return this.connectionState === ConnectionState.CONNECTED
  }
}

// Global singleton instance
const sseManager = new SSEManager()

export function useSSESingleton() {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED
  )
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const accessToken = useAuthStore((state) => state.accessToken)

  useEffect(() => {
    if (!accessToken) {
      console.log('[useSSESingleton] No token, skipping connection')
      return
    }

    console.log('[useSSESingleton] Connecting with token')
    sseManager.connect(accessToken)

    const unsubConn = sseManager.onConnectionChange(setIsConnected)
    const unsubState = sseManager.onStateChange((state) => {
      setConnectionState(state)
      setReconnectAttempts(sseManager.getReconnectAttempts())
    })

    return () => {
      console.log('[useSSESingleton] Component unmounting')
      unsubConn()
      unsubState()
    }
  }, [accessToken])

  return {
    isConnected,
    connectionState,
    reconnectAttempts,
    reconnect: () => {
      if (accessToken) {
        sseManager.disconnect()
        sseManager.connect(accessToken)
      }
    },
    disconnect: () => sseManager.disconnect(),
  }
}

export function useTimelineEventsSingleton() {
  const [jobs, setJobs] = useState<Map<string, TimelineJob>>(new Map())
  const { isConnected, connectionState, reconnectAttempts } = useSSESingleton()

  const handleEvent = useCallback((event: SSEEvent) => {
    const { type, data } = event

    if (type === 'job.started') {
      const job: TimelineJob = {
        id: data.job_id as string,
        pluginName: data.plugin_name as string,
        pluginColor: (data.plugin_color as string) || '#6366F1',
        documentId: data.document_id as string,
        documentName: (data.document_name as string) || 'Unknown',
        progress: 0,
        progressMessage: 'Starting...',
        status: 'running',
        startedAt: new Date(data.started_at as string),
      }
      setJobs((prev) => new Map(prev).set(job.id, job))
    } else if (type === 'job.progress') {
      setJobs((prev) => {
        const newJobs = new Map(prev)
        const existing = newJobs.get(data.job_id as string)
        if (existing) {
          newJobs.set(data.job_id as string, {
            ...existing,
            progress: data.progress as number,
            progressMessage: (data.progress_message as string) || existing.progressMessage,
          })
        }
        return newJobs
      })
    } else if (type === 'job.completed') {
      setJobs((prev) => {
        const newJobs = new Map(prev)
        const existing = newJobs.get(data.job_id as string)
        if (existing) {
          newJobs.set(data.job_id as string, {
            ...existing,
            progress: 100,
            progressMessage: 'Completed',
            status: 'completed',
            endedAt: new Date(data.completed_at as string),
          })
        }
        return newJobs
      })
    } else if (type === 'job.failed') {
      setJobs((prev) => {
        const newJobs = new Map(prev)
        const existing = newJobs.get(data.job_id as string)
        if (existing) {
          newJobs.set(data.job_id as string, {
            ...existing,
            status: 'failed',
            error: data.error_message as string,
            endedAt: new Date(),
          })
        }
        return newJobs
      })
    }
  }, [])

  useEffect(() => {
    console.log('[useTimelineEventsSingleton] Subscribing to events')
    const unsubscribe = sseManager.subscribe(handleEvent)
    return () => {
      console.log('[useTimelineEventsSingleton] Unsubscribing from events')
      unsubscribe()
    }
  }, [handleEvent])

  const clearJobs = useCallback(() => {
    setJobs(new Map())
  }, [])

  const activeJobs = Array.from(jobs.values()).filter((j) => j.status === 'running')
  const recentJobs = Array.from(jobs.values())
    .sort((a, b) => b.startedAt.getTime() - a.startedAt.getTime())
    .slice(0, 50)

  return {
    isConnected,
    connectionState,
    reconnectAttempts,
    jobs,
    activeJobs,
    recentJobs,
    clearJobs,
  }
}
