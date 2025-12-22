// Time ruler component showing time labels

import { useMemo } from 'react'
import type { TimelineViewport } from '../types'
import { formatTimeAgo } from '../utils/timeFormatting'

interface TimelineAxisProps {
  viewport: TimelineViewport
  tickInterval?: number // Interval between ticks in seconds
}

export function TimelineAxis({
  viewport,
  tickInterval,
}: TimelineAxisProps) {
  const ticks = useMemo(() => {
    const result: Array<{ offset: number; label: string; position: number }> =
      []

    const durationSeconds = viewport.duration / 1000
    const now = Date.now()

    // Calculate optimal tick interval based on duration to avoid overlap
    // Aim for ~8-12 ticks across the timeline
    const calculatedInterval = tickInterval || Math.ceil(durationSeconds / 10)

    // Round to nice intervals (30s, 1m, 2m, 5m, 10m, 30m, 1h)
    const niceIntervals = [30, 60, 120, 300, 600, 1800, 3600]
    const optimalInterval = niceIntervals.find(int => int >= calculatedInterval) || calculatedInterval

    // Generate ticks from 0 to duration at optimal interval
    for (let i = 0; i <= durationSeconds; i += optimalInterval) {
      const timeAgo = durationSeconds - i // Seconds from now
      const timestamp = now - timeAgo * 1000
      const position = (timestamp - viewport.startTime) * viewport.pixelsPerMs

      result.push({
        offset: i,
        label: formatTimeAgo(timeAgo),
        position,
      })
    }

    return result
  }, [viewport.duration, viewport.startTime, viewport.pixelsPerMs, tickInterval])

  return (
    <div className="flex items-center h-8 border-t bg-muted/50 sticky bottom-0 z-10">
      <div className="w-32 sm:w-40 flex-shrink-0" /> {/* Spacer for plugin names */}
      <div className="flex-1 relative">
        {ticks.map((tick) => (
          <div
            key={tick.offset}
            className="absolute text-xs text-muted-foreground"
            style={{
              left: `${tick.position}px`,
              transform: 'translateX(-50%)',
            }}
          >
            {tick.label}
          </div>
        ))}
      </div>
    </div>
  )
}
