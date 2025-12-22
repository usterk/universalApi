import { useState, useEffect, useCallback } from 'react'
import { Header } from '@/components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useTimelineEvents } from '@/core/contexts/SSEContext'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/core/api/client'

// New timeline components and hooks
import { TimelineCanvas } from '@/features/timeline/components/TimelineCanvas'
import { TimelineFilters } from '@/features/timeline/components/TimelineFilters'
import { TimelineControls } from '@/features/timeline/components/TimelineControls'
import { EventDetailsPanel } from '@/features/timeline/components/EventDetailsPanel'
import { useTimelineViewport } from '@/features/timeline/hooks/useTimelineViewport'
import { useTimelineFilters } from '@/features/timeline/hooks/useTimelineFilters'
import { useTimelineLayout } from '@/features/timeline/hooks/useTimelineLayout'
import { useEventSelection } from '@/features/timeline/hooks/useEventSelection'

const COLLAPSED_PLUGINS_KEY = 'timeline-collapsed-plugins'

export function Timeline() {
  const { isConnected, jobs } = useTimelineEvents()

  // Collapsed plugin state with localStorage persistence
  const [collapsedPlugins, setCollapsedPlugins] = useState<Set<string>>(() => {
    try {
      const saved = localStorage.getItem(COLLAPSED_PLUGINS_KEY)
      if (saved) {
        return new Set(JSON.parse(saved))
      }
    } catch (error) {
      console.error('Failed to load collapsed plugins:', error)
    }
    return new Set()
  })

  // Persist collapsed plugins to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(
        COLLAPSED_PLUGINS_KEY,
        JSON.stringify(Array.from(collapsedPlugins))
      )
    } catch (error) {
      console.error('Failed to save collapsed plugins:', error)
    }
  }, [collapsedPlugins])

  // Toggle plugin collapse state
  const togglePluginCollapse = useCallback((pluginName: string) => {
    setCollapsedPlugins((prev) => {
      const next = new Set(prev)
      if (next.has(pluginName)) {
        next.delete(pluginName)
      } else {
        next.add(pluginName)
      }
      return next
    })
  }, [])

  // Filter visibility state
  const [showFilters, setShowFilters] = useState(false)

  // Initialize hooks
  const viewportHook = useTimelineViewport(600000, true) // 10 minutes
  const filtersHook = useTimelineFilters()
  const { pluginSections, visibleEventCount } = useTimelineLayout(
    jobs,
    viewportHook.viewport,
    filtersHook.filters,
    collapsedPlugins
  )
  const { selectedEvent, selectEvent, clearSelection } = useEventSelection()

  // Get plugins for colors and legend
  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => api.getPlugins(),
  })

  return (
    <div className="flex flex-col h-full">
      <Header title="Timeline" />

      <div className="p-6 space-y-6 flex-1">
        {/* Connection Status and Filter Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div
                className={`h-2 w-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm">
                {isConnected ? 'Real-time updates active' : 'Reconnecting...'}
              </span>
            </div>
            <Badge variant="secondary">
              {jobs.size} tracked job{jobs.size !== 1 ? 's' : ''}
            </Badge>
            <Badge variant="outline">
              {visibleEventCount} visible event{visibleEventCount !== 1 ? 's' : ''}
            </Badge>
          </div>

          {/* Filter toggle button (when collapsed) */}
          {!showFilters && (
            <TimelineFilters
              filters={filtersHook}
              plugins={plugins}
              isVisible={false}
              onToggleVisibility={() => setShowFilters(true)}
            />
          )}
        </div>

        {/* Filters Panel (when expanded) */}
        {showFilters && (
          <TimelineFilters
            filters={filtersHook}
            plugins={plugins}
            isVisible={true}
            onToggleVisibility={() => setShowFilters(false)}
          />
        )}

        {/* Timeline Controls */}
        <TimelineControls viewport={viewportHook} />

        {/* Timeline Visualization */}
        <Card>
          <CardHeader>
            <CardTitle>Processing Timeline</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <TimelineCanvas
              pluginSections={pluginSections}
              viewport={viewportHook.viewport}
              selectedEventId={selectedEvent?.event.id}
              onEventClick={selectEvent}
              onToggleCollapse={togglePluginCollapse}
              onWidthChange={viewportHook.setWidth}
            />
          </CardContent>
        </Card>

        {/* Legend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Legend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {plugins?.map((plugin) => (
                <div key={plugin.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: plugin.color }}
                  />
                  <span className="text-sm">{plugin.display_name}</span>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span className="text-sm">Failed</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Event Details Panel (slide-in sidebar) */}
      <EventDetailsPanel selectedEvent={selectedEvent} onClose={clearSelection} />
    </div>
  )
}
