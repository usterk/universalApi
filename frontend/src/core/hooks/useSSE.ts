import { useEffect, useRef, useCallback, useState } from 'react'
import { useAuthStore } from '@/core/stores/auth'
import { api } from '@/core/api/client'

export interface SSEEvent {
  id: string
  type: string
  data: Record<string, unknown>
  timestamp: string
}

export interface TimelineJob {
  id: string
  pluginName: string
  pluginColor: string
  documentId: string
  documentName: string
  progress: number
  progressMessage: string
  status: 'running' | 'completed' | 'failed'
  startedAt: Date
  endedAt?: Date
  error?: string
}

interface UseSSEOptions {
  eventTypes?: string[]
  onEvent?: (event: SSEEvent) => void
  onError?: (error: Event) => void
  autoReconnect?: boolean
  reconnectDelay?: number
}

export function useSSE(options: UseSSEOptions = {}) {
  const {
    eventTypes,
    onEvent,
    onError,
    autoReconnect = true,
    reconnectDelay = 3000,
  } = options

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [events, setEvents] = useState<SSEEvent[]>([])
  const accessToken = useAuthStore((state) => state.accessToken)
  const prevTokenRef = useRef<string | null>(accessToken)

  const connect = useCallback(() => {
    if (!accessToken) {
      console.log('[SSE] No access token available, skipping connection')
      return
    }

    // Build URL with query params
    let url = '/api/v1/events/stream'
    const params = new URLSearchParams()
    params.set('token', accessToken)
    if (eventTypes && eventTypes.length > 0) {
      params.set('types', eventTypes.join(','))
    }
    url += `?${params.toString()}`

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      console.log('[SSE] Connected to event stream')
    }

    // Handler for SSE events
    const handleEvent = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data) as SSEEvent
        setEvents((prev) => [...prev.slice(-99), data])
        onEvent?.(data)
      } catch (error) {
        console.error('[SSE] Failed to parse event:', error, event)
      }
    }

    // Listen to default message events (no event type)
    eventSource.onmessage = handleEvent

    // Listen to specific event types if provided
    if (eventTypes && eventTypes.length > 0) {
      eventTypes.forEach((type) => {
        eventSource.addEventListener(type, handleEvent)
      })
    }

    // Listen to keepalive events
    eventSource.addEventListener('keepalive', () => {
      console.log('[SSE] Keepalive received')
    })

    eventSource.onerror = async (event) => {
      console.error('[SSE] Connection error:', event)
      setIsConnected(false)
      onError?.(event)

      // If EventSource failed, it might be due to expired token
      // Try to refresh the token by making an authenticated API call
      // which will trigger the axios interceptor
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken && eventSource.readyState === EventSource.CLOSED) {
        try {
          console.log('[SSE] Attempting to refresh token...')
          await api.me() // This will trigger token refresh if needed
          console.log('[SSE] Token refreshed, will reconnect')
        } catch (error) {
          console.error('[SSE] Token refresh failed:', error)
          // If refresh fails, user will be logged out by axios interceptor
          return
        }
      }

      if (autoReconnect) {
        console.log(`[SSE] Reconnecting in ${reconnectDelay}ms...`)
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, reconnectDelay)
      }
    }
  }, [accessToken, eventTypes, onEvent, onError, autoReconnect, reconnectDelay])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
  }, [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  // Watch for token changes and reconnect
  useEffect(() => {
    if (prevTokenRef.current !== accessToken) {
      console.log('[SSE] Token changed, reconnecting...')
      prevTokenRef.current = accessToken
      disconnect()
      if (accessToken) {
        // Wait a bit before reconnecting with new token
        setTimeout(() => connect(), 500)
      }
    }
  }, [accessToken, connect, disconnect])

  const clearEvents = useCallback(() => {
    setEvents([])
  }, [])

  return {
    isConnected,
    events,
    clearEvents,
    reconnect: connect,
    disconnect,
  }
}

// Hook for timeline-specific events
export function useTimelineEvents() {
  const [jobs, setJobs] = useState<Map<string, TimelineJob>>(new Map())

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

  const { isConnected, events } = useSSE({
    eventTypes: ['job.started', 'job.progress', 'job.completed', 'job.failed'],
    onEvent: handleEvent,
  })

  const clearJobs = useCallback(() => {
    setJobs(new Map())
  }, [])

  const activeJobs = Array.from(jobs.values()).filter((j) => j.status === 'running')
  const recentJobs = Array.from(jobs.values())
    .sort((a, b) => b.startedAt.getTime() - a.startedAt.getTime())
    .slice(0, 50)

  return {
    isConnected,
    events,
    jobs,
    activeJobs,
    recentJobs,
    clearJobs,
  }
}
