// Timeline layout computation hook

import { useMemo } from 'react'
import type { TimelineJob } from '@/core/hooks/useSSE'
import type {
  TimelineEvent,
  TimelineViewport,
  TimelineFilters,
  PluginSection,
  SubLane,
  EventType,
} from '../types'
import { jobToEvent, formatSublaneLabel } from '../types'
import { assignLanes, groupBy } from '../utils/layoutAlgorithm'

// Layout constants
const PLUGIN_HEADER_HEIGHT = 36
const SUBLANE_ROW_HEIGHT = 32
const SUBLANE_PADDING = 4
const PLUGIN_SECTION_PADDING = 8

export interface UseTimelineLayoutResult {
  pluginSections: PluginSection[]
  totalHeight: number
  visibleEventCount: number
}

/**
 * Hook for computing timeline layout with lane assignments
 * Handles filtering, grouping, overlap detection, and height calculation
 */
export function useTimelineLayout(
  jobs: Map<string, TimelineJob>,
  viewport: TimelineViewport,
  filters: TimelineFilters,
  collapsedPlugins: Set<string>
): UseTimelineLayoutResult {
  return useMemo(() => {
    // Convert jobs to events for each event type
    const allEvents: TimelineEvent[] = []

    jobs.forEach((job) => {
      // Create event for the job's current lifecycle stage
      // For now, we'll infer the event type from the job status
      let eventType: EventType

      if (job.status === 'failed') {
        eventType = 'job.failed'
      } else if (job.status === 'completed') {
        eventType = 'job.completed'
      } else if (job.progress > 0) {
        eventType = 'job.progress'
      } else {
        eventType = 'job.started'
      }

      const event = jobToEvent(job, eventType)

      // Filter by time window (with buffer for partial visibility)
      const eventEnd = event.endedAt?.getTime() || Date.now()
      if (
        eventEnd < viewport.startTime ||
        event.startedAt.getTime() > viewport.endTime
      ) {
        return // Skip events outside time window
      }

      // Filter by active filters
      const isPluginEnabled =
        filters.plugins.size === 0 || filters.plugins.has(event.pluginName)
      const isEventTypeEnabled = filters.eventTypes.has(event.eventType)
      const isStatusEnabled = filters.statuses.has(event.status)

      if (isPluginEnabled && isEventTypeEnabled && isStatusEnabled) {
        allEvents.push(event)
      }
    })

    // Group by plugin
    const byPlugin = groupBy(allEvents, (e) => e.pluginName)

    // Build plugin sections
    const sections: PluginSection[] = []
    let totalHeight = 0

    byPlugin.forEach((pluginEvents, pluginName) => {
      // Group by event type (sublanes)
      const bySublane = groupBy(pluginEvents, (e) => e.eventType)

      const sublanes: SubLane[] = []

      // Process each sublane
      bySublane.forEach((sublaneEvents, eventType) => {
        // Assign lanes for overlapping events
        const laneAssignments = assignLanes(sublaneEvents)

        // Apply lane assignments to events
        sublaneEvents.forEach((event) => {
          event.laneIndex = laneAssignments.get(event.id) || 0
        })

        const maxLane = Math.max(...Array.from(laneAssignments.values()), 0)
        const rows = maxLane + 1

        sublanes.push({
          type: eventType,
          label: formatSublaneLabel(eventType),
          events: sublaneEvents,
          rows,
          height: rows * SUBLANE_ROW_HEIGHT + SUBLANE_PADDING,
          isVisible: sublaneEvents.length > 0,
        })
      })

      // Filter to only visible sublanes
      const visibleSublanes = sublanes.filter((sl) => sl.isVisible)

      if (visibleSublanes.length === 0) {
        return // Skip plugins with no visible events
      }

      const isCollapsed = collapsedPlugins.has(pluginName)
      const sublaneHeight = isCollapsed
        ? 0
        : visibleSublanes.reduce((sum, sl) => sum + sl.height, 0)

      const sectionHeight =
        PLUGIN_HEADER_HEIGHT + sublaneHeight + PLUGIN_SECTION_PADDING

      sections.push({
        pluginName,
        pluginColor: pluginEvents[0]?.pluginColor || '#6366F1',
        isCollapsed,
        sublanes: visibleSublanes,
        totalHeight: sectionHeight,
      })

      totalHeight += sectionHeight
    })

    return {
      pluginSections: sections,
      totalHeight,
      visibleEventCount: allEvents.length,
    }
  }, [jobs, viewport.startTime, viewport.endTime, filters, collapsedPlugins])
}
