// Individual event bar visualization component

import { memo } from 'react'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import type { TimelineEvent, TimelineViewport } from '../types'
import { getStatusColor } from '../utils/colorUtils'
import { formatDuration } from '../utils/timeFormatting'

// Constants
const MIN_EVENT_WIDTH = 8
const SUBLANE_ROW_HEIGHT = 32
const SUBLANE_PADDING = 4

interface EventBarProps {
  event: TimelineEvent
  viewport: TimelineViewport
  isSelected?: boolean
  onClick?: (event: TimelineEvent, position: { x: number; y: number }) => void
}

export const EventBar = memo(function EventBar({
  event,
  viewport,
  isSelected = false,
  onClick,
}: EventBarProps) {
  const now = Date.now()

  // Calculate time offsets
  const eventStart = event.startedAt.getTime()

  // For completed/failed events, use endedAt; for running, use now but cap at viewport end
  let eventEnd: number
  if (event.endedAt) {
    eventEnd = event.endedAt.getTime()
  } else if (event.status === 'running') {
    // Running events extend to now, but cap at viewport end
    eventEnd = Math.min(now, viewport.endTime)
  } else {
    // Completed/failed without endedAt - show minimal duration
    eventEnd = eventStart + 1000 // 1 second default
  }

  // X position: distance from viewport start
  const left = (eventStart - viewport.startTime) * viewport.pixelsPerMs

  // Width: duration in pixels, capped at viewport width
  const rawWidth = (eventEnd - eventStart) * viewport.pixelsPerMs
  const maxWidth = viewport.width - left
  const width = Math.max(MIN_EVENT_WIDTH, Math.min(rawWidth, maxWidth))

  // Don't render if completely outside viewport
  if (left > viewport.width || left + width < 0) {
    return null
  }

  // Y position: lane index within sublane
  const top = event.laneIndex * SUBLANE_ROW_HEIGHT + SUBLANE_PADDING / 2

  // Height: fixed row height minus padding
  const height = SUBLANE_ROW_HEIGHT - SUBLANE_PADDING

  // Color based on status
  const backgroundColor = getStatusColor(event.status, event.pluginColor)

  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      onClick(event, { x: e.clientX, y: e.clientY })
    }
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={`absolute rounded cursor-pointer transition-all ${
            isSelected
              ? 'ring-2 ring-white ring-offset-2 ring-offset-background'
              : 'hover:opacity-80'
          }`}
          style={{
            left: `${left}px`,
            top: `${top}px`,
            width: `${width}px`,
            height: `${height}px`,
            backgroundColor,
          }}
          onClick={handleClick}
        />
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <div className="space-y-1">
          <p className="font-medium">{event.documentName}</p>
          {event.progressMessage && (
            <p className="text-xs text-muted-foreground">
              {event.progressMessage}
            </p>
          )}
          <div className="flex gap-2 text-xs flex-wrap">
            <Badge variant="secondary">{event.progress}%</Badge>
            <Badge
              variant={
                event.status === 'completed'
                  ? 'default'
                  : event.status === 'failed'
                  ? 'destructive'
                  : 'secondary'
              }
            >
              {event.status}
            </Badge>
            {event.duration !== undefined && (
              <Badge variant="outline">{formatDuration(event.duration)}</Badge>
            )}
          </div>
          {event.error && (
            <p className="text-xs text-destructive mt-2">{event.error}</p>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  )
})
