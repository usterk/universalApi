// Plugin header component with collapse/expand functionality

import { ChevronDown, ChevronRight, Settings2 } from 'lucide-react'

interface PluginHeaderProps {
  pluginName: string
  pluginColor: string
  isCollapsed: boolean
  eventCount: number
  onToggleCollapse: () => void
  isSystem?: boolean
}

export function PluginHeader({
  pluginName,
  pluginColor,
  isCollapsed,
  eventCount,
  onToggleCollapse,
  isSystem = false,
}: PluginHeaderProps) {
  return (
    <div
      className="flex items-center h-9 bg-muted/20 cursor-pointer hover:bg-muted/30 transition-colors"
      onClick={onToggleCollapse}
    >
      <div className="w-32 sm:w-40 px-2 sm:px-3 text-xs sm:text-sm font-medium flex items-center gap-1 sm:gap-2 flex-shrink-0 overflow-hidden">
        {/* Collapse/Expand Icon */}
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
        )}

        {/* System Gear Icon or Plugin Color Indicator */}
        {isSystem ? (
          <Settings2 className="w-3 h-3 text-emerald-500 flex-shrink-0" />
        ) : (
          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: pluginColor }} />
        )}

        {/* Plugin Name - truncate if too long */}
        <span className="truncate flex-1 min-w-0">{pluginName}</span>

        {/* Event Count Badge - flex-shrink-0 to prevent clipping */}
        {eventCount > 0 && (
          <span className="text-xs text-muted-foreground flex-shrink-0">({eventCount})</span>
        )}
      </div>
      <div className="flex-1" />
    </div>
  )
}
