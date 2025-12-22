// Timeline navigation controls (zoom and pan)

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ZoomIn,
  ZoomOut,
  Play,
  Pause,
} from 'lucide-react'
import type { UseTimelineViewportResult } from '../hooks/useTimelineViewport'

interface TimelineControlsProps {
  viewport: UseTimelineViewportResult
}

// Zoom presets in milliseconds
const ZOOM_PRESETS = [
  { label: '5m', value: 5 * 60 * 1000 },
  { label: '10m', value: 10 * 60 * 1000 },
  { label: '30m', value: 30 * 60 * 1000 },
  { label: '1h', value: 60 * 60 * 1000 },
  { label: '6h', value: 6 * 60 * 60 * 1000 },
]

// Pan intervals
const PAN_SHORT = 10 * 60 * 1000 // 10 minutes
const PAN_LONG = 60 * 60 * 1000 // 1 hour

export function TimelineControls({ viewport }: TimelineControlsProps) {
  const currentDuration = viewport.viewport.duration

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 flex-wrap">
      {/* Live/Pause Toggle */}
      <div className="flex items-center gap-2">
        <Button
          variant={viewport.isLive ? 'default' : 'outline'}
          size="sm"
          onClick={() =>
            viewport.isLive ? viewport.setIsLive(false) : viewport.resetToNow()
          }
          className="gap-2"
        >
          {viewport.isLive ? (
            <>
              <Pause className="w-4 h-4" />
              Live
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Paused
            </>
          )}
        </Button>
      </div>

      {/* Pan Controls */}
      <div className="flex items-center gap-1 border rounded-md p-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => viewport.panBy(-PAN_LONG)}
          title="Pan 1 hour backward"
        >
          <ChevronsLeft className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => viewport.panBy(-PAN_SHORT)}
          title="Pan 10 minutes backward"
        >
          <ChevronLeft className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => viewport.panBy(PAN_SHORT)}
          title="Pan 10 minutes forward"
          disabled={viewport.isLive}
        >
          <ChevronRight className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => viewport.resetToNow()}
          title="Jump to now"
        >
          <ChevronsRight className="w-4 h-4" />
        </Button>
      </div>

      {/* Zoom Presets */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Zoom:</span>
        <div className="flex items-center gap-1 border rounded-md p-1">
          {ZOOM_PRESETS.map((preset) => (
            <Button
              key={preset.label}
              variant={currentDuration === preset.value ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => viewport.zoomTo(preset.value)}
            >
              {preset.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Quick Zoom In/Out */}
      <div className="flex items-center gap-1 border rounded-md p-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            const currentIndex = ZOOM_PRESETS.findIndex(
              (p) => p.value === currentDuration
            )
            if (currentIndex > 0) {
              viewport.zoomTo(ZOOM_PRESETS[currentIndex - 1].value)
            }
          }}
          disabled={currentDuration <= ZOOM_PRESETS[0].value}
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            const currentIndex = ZOOM_PRESETS.findIndex(
              (p) => p.value === currentDuration
            )
            if (currentIndex < ZOOM_PRESETS.length - 1) {
              viewport.zoomTo(ZOOM_PRESETS[currentIndex + 1].value)
            }
          }}
          disabled={currentDuration >= ZOOM_PRESETS[ZOOM_PRESETS.length - 1].value}
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
      </div>

      {/* Current Duration Badge */}
      <Badge variant="outline">
        Window:{' '}
        {ZOOM_PRESETS.find((p) => p.value === currentDuration)?.label || 'Custom'}
      </Badge>
    </div>
  )
}
