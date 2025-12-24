// Real-time playhead cursor showing "now" position

import { useState, useEffect } from 'react'
import type { TimelineViewport } from '../types'

interface PlayheadCursorProps {
  viewport: TimelineViewport
}

export function PlayheadCursor({ viewport }: PlayheadCursorProps) {
  const [now, setNow] = useState(Date.now())

  // Update "now" every second
  useEffect(() => {
    const interval = setInterval(() => {
      setNow(Date.now())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Calculate playhead position
  const playheadX = (now - viewport.startTime) * viewport.pixelsPerMs

  // Only show playhead if it's within the visible viewport (with small margin)
  const MARGIN = 2 // pixels
  if (playheadX < -MARGIN || playheadX > viewport.width + MARGIN) {
    return null
  }

  // Clamp position to viewport bounds to prevent overflow
  const clampedX = Math.max(0, Math.min(playheadX, viewport.width))

  // When at the right edge, shift label left so it stays fully visible
  const isAtRightEdge = playheadX >= viewport.width - 30
  const labelTransform = isAtRightEdge ? 'translateX(-100%)' : 'translateX(-50%)'

  return (
    <>
      {/* Vertical line */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none z-30"
        style={{
          left: `${clampedX}px`,
          boxShadow: '0 0 4px rgba(239, 68, 68, 0.5)',
        }}
      />

      {/* "Now" label at the top */}
      <div
        className="absolute top-0 pointer-events-none z-30"
        style={{
          left: `${clampedX}px`,
          transform: labelTransform,
        }}
      >
        <div className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-b shadow-md font-medium whitespace-nowrap">
          Now
        </div>
      </div>
    </>
  )
}
