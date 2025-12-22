import { createContext, useContext, ReactNode, useEffect } from 'react'
import { useTimelineEventsSingleton, ConnectionState } from '@/core/hooks/useSSESingleton'
import type { TimelineJob } from '@/core/hooks/useSSE'
import { log } from '@/core/utils/logger'

interface SSEContextValue {
  isConnected: boolean
  connectionState: ConnectionState
  reconnectAttempts: number
  jobs: Map<string, TimelineJob>
  activeJobs: TimelineJob[]
  recentJobs: TimelineJob[]
  clearJobs: () => void
}

const SSEContext = createContext<SSEContextValue | null>(null)

let providerCount = 0

export function SSEProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    providerCount++
    const currentId = providerCount
    log.debug('sse_provider_mounted', { provider_id: currentId })
    return () => {
      log.debug('sse_provider_unmounted', { provider_id: currentId })
    }
  }, [])

  const timelineData = useTimelineEventsSingleton()

  return <SSEContext.Provider value={timelineData}>{children}</SSEContext.Provider>
}

export function useTimelineEvents() {
  const context = useContext(SSEContext)
  if (!context) {
    throw new Error('useTimelineEvents must be used within SSEProvider')
  }
  return context
}

export function useSSEConnection() {
  const context = useContext(SSEContext)
  if (!context) {
    throw new Error('useSSEConnection must be used within SSEProvider')
  }
  return {
    isConnected: context.isConnected,
    events: context.events,
    reconnect: context.reconnect,
    disconnect: context.disconnect,
  }
}
