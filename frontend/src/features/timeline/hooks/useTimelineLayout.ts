// Timeline layout computation hook (simplified - no sublanes)

import { useMemo } from 'react'
import type { TimelineJob } from '@/core/hooks/useSSE'
import type {
  TimelineEvent,
  TimelineViewport,
  TimelineFilters,
  PluginSection,
  SystemActivity,
} from '../types'
import { jobToEvent, systemActivityToEvent } from '../types'
import { assignLanes, groupBy } from '../utils/layoutAlgorithm'

// Layout constants
const PLUGIN_HEADER_HEIGHT = 36
const ROW_HEIGHT = 32
const SECTION_PADDING = 8

export interface UseTimelineLayoutResult {
  pluginSections: PluginSection[]
  totalHeight: number
  visibleEventCount: number
}

/**
 * Hook for computing timeline layout with lane assignments
 * Simplified: one row per plugin, no sublanes
 */
export function useTimelineLayout(
  jobs: Map<string, TimelineJob>,
  systemActivities: Map<string, SystemActivity>,
  documentEvents: Map<string, import('../types').DocumentEvent>,
  viewport: TimelineViewport,
  filters: TimelineFilters,
  collapsedPlugins: Set<string>
): UseTimelineLayoutResult {
  return useMemo(() => {
    const allEvents: TimelineEvent[] = []
    const systemEvents: TimelineEvent[] = []

    // Process system activities first
    systemActivities.forEach((activity) => {
      const event = systemActivityToEvent(activity)

      // Filter by time window
      const eventEnd = event.endedAt?.getTime() || Date.now()
      if (
        eventEnd < viewport.startTime ||
        event.startedAt.getTime() > viewport.endTime
      ) {
        return // Skip events outside time window
      }

      // Apply filters (System section uses 'System' as plugin name)
      const isSystemEnabled = !filters.plugins.has('System')
      const isStatusEnabled = filters.statuses.has(event.status)

      if (isSystemEnabled && isStatusEnabled) {
        systemEvents.push(event)
      }
    })

    // Process job events
    jobs.forEach((job) => {
      const event = jobToEvent(job)

      // Filter by time window
      const eventEnd = event.endedAt?.getTime() || Date.now()
      if (
        eventEnd < viewport.startTime ||
        event.startedAt.getTime() > viewport.endTime
      ) {
        return // Skip events outside time window
      }

      // Apply filters
      // Plugins IN filters.plugins are DISABLED (hidden)
      const isPluginEnabled = !filters.plugins.has(event.pluginName)
      const isStatusEnabled = filters.statuses.has(event.status)

      if (isPluginEnabled && isStatusEnabled) {
        allEvents.push(event)
      }
    })

    // Group by plugin
    const byPlugin = groupBy(allEvents, (e) => e.pluginName)

    // Build plugin sections
    const sections: PluginSection[] = []
    let totalHeight = 0

    // Add System section first (if there are system events)
    if (systemEvents.length > 0) {
      const laneAssignments = assignLanes(systemEvents)
      systemEvents.forEach((event) => {
        event.laneIndex = laneAssignments.get(event.id) || 0
      })

      const maxLane = Math.max(...Array.from(laneAssignments.values()), 0)
      const rows = maxLane + 1

      const isCollapsed = collapsedPlugins.has('System')
      const contentHeight = isCollapsed ? 0 : rows * ROW_HEIGHT + SECTION_PADDING
      const sectionHeight = PLUGIN_HEADER_HEIGHT + contentHeight

      sections.push({
        pluginName: 'System',
        pluginColor: '#22C55E', // System green
        isCollapsed,
        events: systemEvents,
        rows: isCollapsed ? 0 : rows,
        totalHeight: sectionHeight,
        isSystem: true,
      })

      totalHeight += sectionHeight
    }

    // Add Documents section
    if (documentEvents.size > 0) {
      const docEventsArray = Array.from(documentEvents.values())

      // Filter by time window
      const filteredDocEvents = docEventsArray.filter((event) => {
        const eventTime = event.timestamp.getTime()
        return eventTime >= viewport.startTime && eventTime <= viewport.endTime
      })

      if (filteredDocEvents.length > 0) {
        const isCollapsed = collapsedPlugins.has('Documents')
        const rows = 1
        const contentHeight = isCollapsed ? 0 : rows * ROW_HEIGHT + SECTION_PADDING
        const sectionHeight = PLUGIN_HEADER_HEIGHT + contentHeight

        sections.push({
          pluginName: 'Documents',
          pluginColor: '#F59E0B',
          isCollapsed,
          events: [],
          documentEvents: filteredDocEvents,
          rows: isCollapsed ? 0 : rows,
          totalHeight: sectionHeight,
          isDocuments: true,
        })

        totalHeight += sectionHeight
      }
    }

    // Add plugin sections
    byPlugin.forEach((pluginEvents, pluginName) => {
      if (pluginEvents.length === 0) return

      // Assign lanes for overlapping events (single pool, no sublanes)
      const laneAssignments = assignLanes(pluginEvents)

      // Apply lane assignments to events
      pluginEvents.forEach((event) => {
        event.laneIndex = laneAssignments.get(event.id) || 0
      })

      const maxLane = Math.max(...Array.from(laneAssignments.values()), 0)
      const rows = maxLane + 1

      const isCollapsed = collapsedPlugins.has(pluginName)
      const contentHeight = isCollapsed ? 0 : rows * ROW_HEIGHT + SECTION_PADDING
      const sectionHeight = PLUGIN_HEADER_HEIGHT + contentHeight

      sections.push({
        pluginName,
        pluginColor: pluginEvents[0]?.pluginColor || '#6366F1',
        isCollapsed,
        events: pluginEvents,
        rows: isCollapsed ? 0 : rows,
        totalHeight: sectionHeight,
      })

      totalHeight += sectionHeight
    })

    return {
      pluginSections: sections,
      totalHeight,
      visibleEventCount: allEvents.length + systemEvents.length,
    }
  }, [jobs, systemActivities, documentEvents, viewport.startTime, viewport.endTime, filters, collapsedPlugins])
}
