// Timeline filters state management hook

import { useState, useCallback, useEffect } from 'react'
import type { TimelineFilters, EventType, JobStatus } from '../types'

const STORAGE_KEY = 'timeline-filters'

// Default filters (all enabled)
const DEFAULT_FILTERS: TimelineFilters = {
  plugins: new Set<string>(),
  eventTypes: new Set<EventType>([
    'job.started',
    'job.progress',
    'job.completed',
    'job.failed',
  ]),
  statuses: new Set<JobStatus>(['running', 'completed', 'failed']),
}

export interface UseTimelineFiltersResult {
  filters: TimelineFilters
  togglePlugin: (pluginName: string) => void
  toggleEventType: (eventType: EventType) => void
  toggleStatus: (status: JobStatus) => void
  setPlugins: (plugins: Set<string>) => void
  setEventTypes: (eventTypes: Set<EventType>) => void
  setStatuses: (statuses: Set<JobStatus>) => void
  clearAll: () => void
  selectAll: (availablePlugins: string[]) => void
  isPluginEnabled: (pluginName: string) => boolean
  isEventTypeEnabled: (eventType: EventType) => boolean
  isStatusEnabled: (status: JobStatus) => boolean
  activeFilterCount: number
}

/**
 * Hook for managing timeline filter state
 * Persists filter preferences to localStorage
 */
export function useTimelineFilters(): UseTimelineFiltersResult {
  const [filters, setFilters] = useState<TimelineFilters>(() => {
    // Load from localStorage
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        return {
          plugins: new Set(parsed.plugins || []),
          eventTypes: new Set(parsed.eventTypes || DEFAULT_FILTERS.eventTypes),
          statuses: new Set(parsed.statuses || DEFAULT_FILTERS.statuses),
        }
      }
    } catch (error) {
      console.error('Failed to load timeline filters:', error)
    }

    return DEFAULT_FILTERS
  })

  // Persist to localStorage whenever filters change
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          plugins: Array.from(filters.plugins),
          eventTypes: Array.from(filters.eventTypes),
          statuses: Array.from(filters.statuses),
        })
      )
    } catch (error) {
      console.error('Failed to save timeline filters:', error)
    }
  }, [filters])

  const togglePlugin = useCallback((pluginName: string) => {
    setFilters((prev) => {
      const newPlugins = new Set(prev.plugins)
      if (newPlugins.has(pluginName)) {
        newPlugins.delete(pluginName)
      } else {
        newPlugins.add(pluginName)
      }
      return { ...prev, plugins: newPlugins }
    })
  }, [])

  const toggleEventType = useCallback((eventType: EventType) => {
    setFilters((prev) => {
      const newEventTypes = new Set(prev.eventTypes)
      if (newEventTypes.has(eventType)) {
        newEventTypes.delete(eventType)
      } else {
        newEventTypes.add(eventType)
      }
      return { ...prev, eventTypes: newEventTypes }
    })
  }, [])

  const toggleStatus = useCallback((status: JobStatus) => {
    setFilters((prev) => {
      const newStatuses = new Set(prev.statuses)
      if (newStatuses.has(status)) {
        newStatuses.delete(status)
      } else {
        newStatuses.add(status)
      }
      return { ...prev, statuses: newStatuses }
    })
  }, [])

  const setPlugins = useCallback((plugins: Set<string>) => {
    setFilters((prev) => ({ ...prev, plugins }))
  }, [])

  const setEventTypes = useCallback((eventTypes: Set<EventType>) => {
    setFilters((prev) => ({ ...prev, eventTypes }))
  }, [])

  const setStatuses = useCallback((statuses: Set<JobStatus>) => {
    setFilters((prev) => ({ ...prev, statuses }))
  }, [])

  const clearAll = useCallback(() => {
    setFilters({
      plugins: new Set(),
      eventTypes: new Set(),
      statuses: new Set(),
    })
  }, [])

  const selectAll = useCallback((availablePlugins: string[]) => {
    setFilters({
      plugins: new Set(availablePlugins),
      eventTypes: new Set<EventType>([
        'job.started',
        'job.progress',
        'job.completed',
        'job.failed',
      ]),
      statuses: new Set<JobStatus>(['running', 'completed', 'failed']),
    })
  }, [])

  const isPluginEnabled = useCallback(
    (pluginName: string) => {
      // Empty set means all plugins enabled
      return filters.plugins.size === 0 || filters.plugins.has(pluginName)
    },
    [filters.plugins]
  )

  const isEventTypeEnabled = useCallback(
    (eventType: EventType) => filters.eventTypes.has(eventType),
    [filters.eventTypes]
  )

  const isStatusEnabled = useCallback(
    (status: JobStatus) => filters.statuses.has(status),
    [filters.statuses]
  )

  // Count active filters (excluding "all")
  const activeFilterCount =
    (filters.plugins.size > 0 ? 1 : 0) +
    (filters.eventTypes.size < 4 ? 1 : 0) +
    (filters.statuses.size < 3 ? 1 : 0)

  return {
    filters,
    togglePlugin,
    toggleEventType,
    toggleStatus,
    setPlugins,
    setEventTypes,
    setStatuses,
    clearAll,
    selectAll,
    isPluginEnabled,
    isEventTypeEnabled,
    isStatusEnabled,
    activeFilterCount,
  }
}
