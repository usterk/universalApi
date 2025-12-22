// Plugin header component with collapse/expand functionality

import { ChevronDown, ChevronRight } from 'lucide-react'

interface PluginHeaderProps {
  pluginName: string
  pluginColor: string
  isCollapsed: boolean
  eventCount: number
  onToggleCollapse: () => void
}

export function PluginHeader({
  pluginName,
  pluginColor,
  isCollapsed,
  eventCount,
  onToggleCollapse,
}: PluginHeaderProps) {
  return (
    <div
      className="flex items-center h-9 bg-muted/20 cursor-pointer hover:bg-muted/30 transition-colors"
      onClick={onToggleCollapse}
    >
      <div className="w-32 sm:w-40 px-2 sm:px-3 text-xs sm:text-sm font-medium truncate flex items-center gap-1 sm:gap-2 flex-shrink-0">
        {/* Collapse/Expand Icon */}
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        )}

        {/* Plugin Color Indicator */}
        <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: pluginColor }} />

        {/* Plugin Name */}
        <span>{pluginName}</span>

        {/* Event Count Badge */}
        {eventCount > 0 && (
          <span className="text-xs text-muted-foreground ml-auto">({eventCount})</span>
        )}
      </div>
      <div className="flex-1" />
    </div>
  )
}
