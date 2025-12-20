import { createContext, useContext, ReactNode, useEffect } from 'react'
import { useTimelineEventsSingleton } from '@/core/hooks/useSSESingleton'
import type { TimelineJob } from '@/core/hooks/useSSE'

interface SSEContextValue {
  isConnected: boolean
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
    console.log(`[SSEProvider #${currentId}] Mounted`)
    return () => {
      console.log(`[SSEProvider #${currentId}] Unmounted`)
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
