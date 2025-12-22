// Sub-lane component for displaying events of a specific type

import type { SubLane as SubLaneType, TimelineViewport, TimelineEvent } from '../types'
import { EventBar } from './EventBar'

interface SubLaneProps {
  sublane: SubLaneType
  viewport: TimelineViewport
  selectedEventId?: string | null
  onEventClick?: (event: TimelineEvent, position: { x: number; y: number }) => void
}

export function SubLane({
  sublane,
  viewport,
  selectedEventId,
  onEventClick,
}: SubLaneProps) {
  if (!sublane.isVisible) {
    return null
  }

  return (
    <div className="border-t border-muted/30">
      {/* Sub-lane header */}
      <div className="flex items-center" style={{ height: `${sublane.height}px` }}>
        {/* Sub-lane label */}
        <div className="w-32 sm:w-40 px-2 sm:px-4 text-xs text-muted-foreground flex-shrink-0">
          {sublane.label}
        </div>

        {/* Events container */}
        <div className="flex-1 relative" style={{ height: `${sublane.height}px` }}>
          {sublane.events.map((event) => (
            <EventBar
              key={event.id}
              event={event}
              viewport={viewport}
              isSelected={selectedEventId === event.id}
              onClick={onEventClick}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
