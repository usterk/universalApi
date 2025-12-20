import { useEffect, useState, useCallback } from 'react'
import { useAuthStore } from '@/core/stores/auth'
import { api } from '@/core/api/client'
import type { SSEEvent, TimelineJob } from './useSSE'

// Global singleton EventSource connection
class SSEManager {
  private eventSource: EventSource | null = null
  private subscribers: Set<(event: SSEEvent) => void> = new Set()
  private reconnectTimeout: NodeJS.Timeout | null = null
  private disconnectTimeout: NodeJS.Timeout | null = null
  private currentToken: string | null = null
  private isConnecting = false
  private connectionCount = 0

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
      console.log(`[SSEManager #${connId}] Connected`)
      this.notifyConnectionChange(true)
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
    })

    eventSource.onerror = async () => {
      this.isConnecting = false
      console.error(`[SSEManager #${connId}] Connection error`)
      this.notifyConnectionChange(false)

      // Try to refresh token
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken && eventSource.readyState === EventSource.CLOSED) {
        try {
          console.log('[SSEManager] Attempting token refresh...')
          await api.me()
          const newToken = useAuthStore.getState().accessToken
          if (newToken) {
            console.log('[SSEManager] Token refreshed, will reconnect')
            this.scheduleReconnect(newToken)
            return
          }
        } catch (error) {
          console.error('[SSEManager] Token refresh failed:', error)
          return
        }
      }

      // Auto-reconnect
      this.scheduleReconnect(token)
    }
  }

  private scheduleReconnect(token: string) {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
    }
    this.reconnectTimeout = setTimeout(() => {
      console.log('[SSEManager] Auto-reconnecting...')
      this.connect(token)
    }, 3000)
  }

  disconnect() {
    console.log('[SSEManager] Disconnecting')
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
    this.notifyConnectionChange(false)
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

  private connectionListeners: Set<(connected: boolean) => void> = new Set()

  onConnectionChange(callback: (connected: boolean) => void): () => void {
    this.connectionListeners.add(callback)
    // Immediately notify of current state
    callback(this.eventSource?.readyState === EventSource.OPEN)
    return () => {
      this.connectionListeners.delete(callback)
    }
  }

  private notifyConnectionChange(connected: boolean) {
    this.connectionListeners.forEach((callback) => callback(connected))
  }

  isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN
  }
}

// Global singleton instance
const sseManager = new SSEManager()

export function useSSESingleton() {
  const [isConnected, setIsConnected] = useState(false)
  const accessToken = useAuthStore((state) => state.accessToken)

  useEffect(() => {
    if (!accessToken) {
      console.log('[useSSESingleton] No token, skipping connection')
      return
    }

    console.log('[useSSESingleton] Connecting with token')
    sseManager.connect(accessToken)

    const unsubscribeConnection = sseManager.onConnectionChange(setIsConnected)

    return () => {
      console.log('[useSSESingleton] Component unmounting')
      unsubscribeConnection()
    }
  }, [accessToken])

  return {
    isConnected,
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
  const { isConnected } = useSSESingleton()

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
    jobs,
    activeJobs,
    recentJobs,
    clearJobs,
  }
}
