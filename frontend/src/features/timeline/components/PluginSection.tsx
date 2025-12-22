// Plugin section component with sublanes for different event types

import type {
  PluginSection as PluginSectionType,
  TimelineViewport,
  TimelineEvent,
} from '../types'
import { SubLane } from './SubLane'
import { PluginHeader } from './PluginHeader'

interface PluginSectionProps {
  section: PluginSectionType
  viewport: TimelineViewport
  selectedEventId?: string | null
  onEventClick?: (event: TimelineEvent, position: { x: number; y: number }) => void
  onToggleCollapse?: (pluginName: string) => void
}

export function PluginSection({
  section,
  viewport,
  selectedEventId,
  onEventClick,
  onToggleCollapse,
}: PluginSectionProps) {
  // Count total events in all sublanes
  const eventCount = section.sublanes.reduce(
    (sum, sublane) => sum + sublane.events.length,
    0
  )

  return (
    <div className="border-b">
      {/* Plugin Header with collapse/expand */}
      <PluginHeader
        pluginName={section.pluginName}
        pluginColor={section.pluginColor}
        isCollapsed={section.isCollapsed}
        eventCount={eventCount}
        onToggleCollapse={() => onToggleCollapse?.(section.pluginName)}
      />

      {/* Sublanes (only shown when not collapsed) */}
      {!section.isCollapsed &&
        section.sublanes.map((sublane) => (
          <SubLane
            key={sublane.type}
            sublane={sublane}
            viewport={viewport}
            selectedEventId={selectedEventId}
            onEventClick={onEventClick}
          />
        ))}
    </div>
  )
}
