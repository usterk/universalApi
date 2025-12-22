// Event details panel - shows full event information in a sidebar

import { X, ExternalLink, Clock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { SelectedEvent } from '../types'
import { formatDuration, formatShortDate } from '../utils/timeFormatting'

interface EventDetailsPanelProps {
  selectedEvent: SelectedEvent | null
  onClose: () => void
}

export function EventDetailsPanel({
  selectedEvent,
  onClose,
}: EventDetailsPanelProps) {
  if (!selectedEvent) {
    return null
  }

  const { event } = selectedEvent

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Slide-in Panel */}
      <div className="fixed right-0 top-0 bottom-0 w-96 bg-background border-l shadow-lg z-50 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-background border-b p-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Event Details</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Document Name */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1">
              Document
            </h3>
            <p className="text-base font-medium">{event.documentName}</p>
            <Button
              variant="link"
              size="sm"
              className="px-0 h-auto"
              onClick={() => {
                // TODO: Navigate to document page
                console.log('Navigate to document:', event.documentId)
              }}
            >
              View document <ExternalLink className="w-3 h-3 ml-1" />
            </Button>
          </div>

          {/* Plugin */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1">
              Plugin
            </h3>
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: event.pluginColor }}
              />
              <span>{event.pluginName}</span>
            </div>
          </div>

          {/* Event Type */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1">
              Event Type
            </h3>
            <Badge variant="outline">{event.sublaneType}</Badge>
          </div>

          {/* Status */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1">
              Status
            </h3>
            <Badge
              variant={
                event.status === 'completed'
                  ? 'default'
                  : event.status === 'failed'
                  ? 'destructive'
                  : 'secondary'
              }
            >
              {event.status}
            </Badge>
          </div>

          {/* Progress */}
          {event.status === 'running' && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-2">
                Progress
              </h3>
              <Progress value={event.progress} className="mb-1" />
              <p className="text-sm text-muted-foreground">
                {event.progress}% - {event.progressMessage || 'Processing...'}
              </p>
            </div>
          )}

          {/* Progress Message (for completed/failed) */}
          {event.status !== 'running' && event.progressMessage && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Message
              </h3>
              <p className="text-sm">{event.progressMessage}</p>
            </div>
          )}

          {/* Error */}
          {event.error && (
            <Card className="border-destructive">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2 text-destructive">
                  <AlertCircle className="w-4 h-4" />
                  Error
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm font-mono bg-muted p-2 rounded">
                  {event.error}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Timing */}
          <div className="space-y-2">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Started At
              </h3>
              <div className="flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4" />
                {formatShortDate(event.startedAt)}
              </div>
            </div>

            {event.endedAt && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">
                  Ended At
                </h3>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4" />
                  {formatShortDate(event.endedAt)}
                </div>
              </div>
            )}

            {event.duration !== undefined && (
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">
                  Duration
                </h3>
                <p className="text-sm">{formatDuration(event.duration)}</p>
              </div>
            )}
          </div>

          {/* IDs */}
          <div className="space-y-2 pt-4 border-t">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Job ID
              </h3>
              <code className="text-xs bg-muted px-2 py-1 rounded">
                {event.jobId}
              </code>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-1">
                Document ID
              </h3>
              <code className="text-xs bg-muted px-2 py-1 rounded">
                {event.documentId}
              </code>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
