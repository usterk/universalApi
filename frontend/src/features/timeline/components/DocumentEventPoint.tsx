import { memo } from 'react'
import { FileUp, FileEdit, Trash2 } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Badge } from '@/components/ui/badge'
import type { DocumentEvent, TimelineViewport } from '../types'
import { formatFileSize } from '@/pages/Documents'
import { format } from 'date-fns'

const EVENT_ICONS = {
  'document.created': FileUp,
  'document.updated': FileEdit,
  'document.deleted': Trash2,
}

const EVENT_COLORS = {
  'document.created': '#10B981',
  'document.updated': '#F59E0B',
  'document.deleted': '#EF4444',
}

interface DocumentEventPointProps {
  event: DocumentEvent
  viewport: TimelineViewport
  onClick?: (event: DocumentEvent) => void
}

export const DocumentEventPoint = memo(function DocumentEventPoint({
  event,
  viewport,
  onClick,
}: DocumentEventPointProps) {
  const eventTime = event.timestamp.getTime()
  const left = (eventTime - viewport.startTime) * viewport.pixelsPerMs

  if (left < 0 || left > viewport.width) {
    return null
  }

  const Icon = EVENT_ICONS[event.eventType]
  const color = EVENT_COLORS[event.eventType]

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className="absolute cursor-pointer transition-all hover:scale-125"
          style={{
            left: `${left}px`,
            top: '8px',
            width: '24px',
            height: '24px',
          }}
          onClick={() => onClick?.(event)}
        >
          <div
            className="w-full h-full rounded-full flex items-center justify-center border-2 border-background shadow-sm"
            style={{ backgroundColor: color }}
          >
            <Icon className="w-3 h-3 text-white" />
          </div>
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-xs">
        <div className="space-y-1">
          <p className="font-medium">{event.documentName}</p>
          <div className="flex gap-2 text-xs flex-wrap">
            <Badge variant="secondary">{event.documentType}</Badge>
            <Badge variant="outline">{formatFileSize(event.sizeBytes)}</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {format(event.timestamp, 'PPp')}
          </p>
        </div>
      </TooltipContent>
    </Tooltip>
  )
})
