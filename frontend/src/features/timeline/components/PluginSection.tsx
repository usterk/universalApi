// Plugin section component (simplified - no sublanes)

import type {
  PluginSection as PluginSectionType,
  TimelineViewport,
  TimelineEvent,
} from '../types'
import { PluginHeader } from './PluginHeader'
import { EventBar } from './EventBar'
import { DocumentEventPoint } from './DocumentEventPoint'

// Layout constants
const ROW_HEIGHT = 32
const SECTION_PADDING = 8

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
  const contentHeight = section.rows * ROW_HEIGHT + SECTION_PADDING

  return (
    <div className="border-b">
      {/* Plugin Header with collapse/expand */}
      <PluginHeader
        pluginName={section.pluginName}
        pluginColor={section.pluginColor}
        isCollapsed={section.isCollapsed}
        eventCount={section.events.length}
        onToggleCollapse={() => onToggleCollapse?.(section.pluginName)}
        isSystem={section.isSystem}
      />

      {/* Events container (only shown when not collapsed) */}
      {!section.isCollapsed && (
        <div className="border-t border-muted/30">
          <div className="flex items-start" style={{ height: `${contentHeight}px` }}>
            {/* Empty spacer for plugin name column */}
            <div className="w-32 sm:w-40 flex-shrink-0" />

            {/* Events render area */}
            <div className="flex-1 relative" style={{ height: `${contentHeight}px` }}>
              {section.events.map((event) => (
                <EventBar
                  key={event.id}
                  event={event}
                  viewport={viewport}
                  isSelected={selectedEventId === event.id}
                  onClick={onEventClick}
                />
              ))}

              {/* Document events (if this is Documents section) */}
              {section.isDocuments && section.documentEvents && (
                section.documentEvents.map((event) => (
                  <DocumentEventPoint
                    key={event.id}
                    event={event}
                    viewport={viewport}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
