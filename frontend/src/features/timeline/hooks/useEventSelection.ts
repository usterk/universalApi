// Event selection state management hook

import { useState, useCallback } from 'react'
import type { SelectedEvent, TimelineEvent } from '../types'

export interface UseEventSelectionResult {
  selectedEvent: SelectedEvent | null
  selectEvent: (event: TimelineEvent, position: { x: number; y: number }) => void
  clearSelection: () => void
  isEventSelected: (eventId: string) => boolean
}

/**
 * Hook for managing event selection state
 * Used for showing event details panel
 */
export function useEventSelection(): UseEventSelectionResult {
  const [selectedEvent, setSelectedEvent] = useState<SelectedEvent | null>(null)

  const selectEvent = useCallback(
    (event: TimelineEvent, position: { x: number; y: number }) => {
      setSelectedEvent({ event, position })
    },
    []
  )

  const clearSelection = useCallback(() => {
    setSelectedEvent(null)
  }, [])

  const isEventSelected = useCallback(
    (eventId: string) => selectedEvent?.event.id === eventId,
    [selectedEvent]
  )

  return {
    selectedEvent,
    selectEvent,
    clearSelection,
    isEventSelected,
  }
}
