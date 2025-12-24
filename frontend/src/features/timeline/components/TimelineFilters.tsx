// Timeline filter controls component

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Filter, X } from 'lucide-react'
import type { UseTimelineFiltersResult } from '../hooks/useTimelineFilters'
import type { EventType, JobStatus } from '../types'

interface TimelineFiltersProps {
  filters: UseTimelineFiltersResult
  plugins: Array<{ name: string; display_name: string; color: string }> | undefined
  isVisible?: boolean
  onToggleVisibility?: () => void
}

// Only show job event types in filter UI (system events use status filter)
const EVENT_TYPE_LABELS: Partial<Record<EventType, string>> = {
  'job.started': 'Starting',
  'job.progress': 'Processing',
  'job.completed': 'Completed',
  'job.failed': 'Failed',
}

const STATUS_LABELS: Record<JobStatus, string> = {
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
}

export function TimelineFilters({
  filters,
  plugins,
  isVisible = true,
  onToggleVisibility,
}: TimelineFiltersProps) {
  const allPlugins = plugins?.map((p) => p.name) || []

  if (!isVisible) {
    return (
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleVisibility}
          className="gap-2"
        >
          <Filter className="w-4 h-4" />
          Filters
          {filters.activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1">
              {filters.activeFilterCount}
            </Badge>
          )}
        </Button>
      </div>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Filter className="w-4 h-4" />
          Filters
          {filters.activeFilterCount > 0 && (
            <Badge variant="secondary">{filters.activeFilterCount} active</Badge>
          )}
        </CardTitle>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => filters.selectAll()}
          >
            Select All
          </Button>
          <Button variant="ghost" size="sm" onClick={() => filters.clearAll(allPlugins)}>
            Clear All
          </Button>
          {onToggleVisibility && (
            <Button variant="ghost" size="sm" onClick={onToggleVisibility}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Plugin Filters */}
        <div>
          <h4 className="text-sm font-medium mb-3">Plugins</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {plugins?.map((plugin) => (
              <div key={plugin.name} className="flex items-center space-x-2">
                <Checkbox
                  id={`plugin-${plugin.name}`}
                  checked={filters.isPluginEnabled(plugin.name)}
                  onCheckedChange={() => filters.togglePlugin(plugin.name)}
                />
                <label
                  htmlFor={`plugin-${plugin.name}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer flex items-center gap-2"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: plugin.color }}
                  />
                  {plugin.display_name}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Event Type Filters */}
        <div>
          <h4 className="text-sm font-medium mb-3">Event Types</h4>
          <div className="grid grid-cols-2 gap-3">
            {(Object.keys(EVENT_TYPE_LABELS) as EventType[]).map((eventType) => (
              <div key={eventType} className="flex items-center space-x-2">
                <Checkbox
                  id={`eventtype-${eventType}`}
                  checked={filters.isEventTypeEnabled(eventType)}
                  onCheckedChange={() => filters.toggleEventType(eventType)}
                />
                <label
                  htmlFor={`eventtype-${eventType}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {EVENT_TYPE_LABELS[eventType]}
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Status Filters */}
        <div>
          <h4 className="text-sm font-medium mb-3">Status</h4>
          <div className="grid grid-cols-3 gap-3">
            {(Object.keys(STATUS_LABELS) as JobStatus[]).map((status) => (
              <div key={status} className="flex items-center space-x-2">
                <Checkbox
                  id={`status-${status}`}
                  checked={filters.isStatusEnabled(status)}
                  onCheckedChange={() => filters.toggleStatus(status)}
                />
                <label
                  htmlFor={`status-${status}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                >
                  {STATUS_LABELS[status]}
                </label>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
