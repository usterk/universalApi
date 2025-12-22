// Timeline viewport state management hook

import { useState, useCallback, useEffect } from 'react'
import type { TimelineViewport } from '../types'

// Constants
const DEFAULT_DURATION = 600000 // 10 minutes in milliseconds
const DEFAULT_WIDTH = 1200 // Base timeline width in pixels

export interface UseTimelineViewportResult {
  viewport: TimelineViewport
  panBy: (deltaMs: number) => void
  zoomTo: (newDuration: number) => void
  resetToNow: () => void
  isLive: boolean
  setIsLive: (live: boolean) => void
  setWidth: (width: number) => void
}

/**
 * Hook for managing timeline viewport state (time window, zoom, pan)
 * @param initialDuration - Initial time window duration in milliseconds
 * @param autoScroll - Whether to automatically scroll to follow "now"
 */
export function useTimelineViewport(
  initialDuration: number = DEFAULT_DURATION,
  autoScroll: boolean = true
): UseTimelineViewportResult {
  const [isLive, setIsLive] = useState(autoScroll)

  const [viewport, setViewport] = useState<TimelineViewport>(() => {
    const now = Date.now()
    return {
      startTime: now - initialDuration,
      endTime: now,
      duration: initialDuration,
      pixelsPerMs: DEFAULT_WIDTH / initialDuration,
      width: DEFAULT_WIDTH,
    }
  })

  // Auto-scroll to follow "now" when in live mode
  useEffect(() => {
    if (!isLive) return

    const interval = setInterval(() => {
      setViewport((prev) => {
        const now = Date.now()
        return {
          ...prev,
          endTime: now,
          startTime: now - prev.duration,
        }
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isLive])

  /**
   * Pan the viewport by a delta in milliseconds
   * Positive delta pans forward in time, negative pans backward
   */
  const panBy = useCallback((deltaMs: number) => {
    setViewport((prev) => ({
      ...prev,
      startTime: prev.startTime + deltaMs,
      endTime: prev.endTime + deltaMs,
    }))

    // Disable live mode when panning backward
    if (deltaMs < 0) {
      setIsLive(false)
    }
  }, [])

  /**
   * Zoom to a new duration (time window size)
   * Maintains the right edge (end time) of the viewport
   */
  const zoomTo = useCallback((newDuration: number) => {
    setViewport((prev) => ({
      ...prev,
      duration: newDuration,
      startTime: prev.endTime - newDuration,
      pixelsPerMs: prev.width / newDuration,
    }))
  }, [])

  /**
   * Reset viewport to show "now" at the right edge
   */
  const resetToNow = useCallback(() => {
    setViewport((prev) => {
      const now = Date.now()
      return {
        ...prev,
        endTime: now,
        startTime: now - prev.duration,
      }
    })
    setIsLive(true)
  }, [])

  /**
   * Update timeline width (for responsive sizing)
   */
  const setWidth = useCallback((width: number) => {
    setViewport((prev) => ({
      ...prev,
      width,
      pixelsPerMs: width / prev.duration,
    }))
  }, [])

  return {
    viewport,
    panBy,
    zoomTo,
    resetToNow,
    isLive,
    setIsLive,
    setWidth,
  }
}
