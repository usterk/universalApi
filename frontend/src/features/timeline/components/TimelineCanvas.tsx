// Main timeline canvas component

import { useRef, useEffect, useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import type {
  PluginSection as PluginSectionType,
  TimelineViewport,
  TimelineEvent,
} from '../types'
import { PluginSection } from './PluginSection'
import { TimelineAxis } from './TimelineAxis'
import { PlayheadCursor } from './PlayheadCursor'

interface TimelineCanvasProps {
  pluginSections: PluginSectionType[]
  viewport: TimelineViewport
  selectedEventId?: string | null
  onEventClick?: (event: TimelineEvent, position: { x: number; y: number }) => void
  onToggleCollapse?: (pluginName: string) => void
  onWidthChange?: (width: number) => void
}

export function TimelineCanvas({
  pluginSections,
  viewport,
  selectedEventId,
  onEventClick,
  onToggleCollapse,
  onWidthChange,
}: TimelineCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(0)

  // Measure container width and update on resize
  useEffect(() => {
    if (!containerRef.current) return

    const updateWidth = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth
        setContainerWidth(width)
        // Notify parent of width change so viewport can be recalculated
        if (onWidthChange) {
          // Responsive plugin name width: 128px on mobile, 160px on desktop
          const isMobile = width < 640
          const PLUGIN_NAME_WIDTH = isMobile ? 128 : 160
          const HORIZONTAL_PADDING = 32 // px-4 = 16px left + 16px right
          const timelineWidth = Math.max(400, width - PLUGIN_NAME_WIDTH - HORIZONTAL_PADDING)
          onWidthChange(timelineWidth)
        }
      }
    }

    updateWidth()

    const resizeObserver = new ResizeObserver(updateWidth)
    resizeObserver.observe(containerRef.current)

    return () => resizeObserver.disconnect()
  }, [onWidthChange])

  // Calculate total width needed (viewport width + plugin name column)
  // Use responsive width: 128px on mobile, 160px on desktop
  const isMobile = containerWidth > 0 && containerWidth < 640
  const PLUGIN_NAME_WIDTH = isMobile ? 128 : 160
  const totalWidth = viewport.width + PLUGIN_NAME_WIDTH

  return (
    <div ref={containerRef} className="w-full px-4">
      <ScrollArea className="w-full">
        <div className="relative" style={{ width: `${totalWidth}px` }}>
        {/* Plugin Sections */}
        {pluginSections.length > 0 ? (
          <>
            {pluginSections.map((section) => (
              <PluginSection
                key={section.pluginName}
                section={section}
                viewport={viewport}
                selectedEventId={selectedEventId}
                onEventClick={onEventClick}
                onToggleCollapse={onToggleCollapse}
              />
            ))}

            {/* Playhead Cursor (absolute positioned overlay) */}
            <div
              className="absolute top-0 bottom-0 pointer-events-none left-32 sm:left-40 overflow-visible"
              style={{ width: `${viewport.width}px` }}
            >
              <PlayheadCursor viewport={viewport} />
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No processing activity in the current time window
          </div>
        )}

        {/* Time Axis */}
        {pluginSections.length > 0 && <TimelineAxis viewport={viewport} />}
        </div>
      </ScrollArea>
    </div>
  )
}
