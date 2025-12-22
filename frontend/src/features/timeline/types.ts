// Timeline feature TypeScript type definitions

import type { TimelineJob } from '@/core/hooks/useSSE'

// Event types from SSE
export type EventType =
  | 'job.started'
  | 'job.progress'
  | 'job.completed'
  | 'job.failed'

// Job status
export type JobStatus = 'running' | 'completed' | 'failed'

// Extended timeline event with layout information
export interface TimelineEvent {
  id: string
  jobId: string
  pluginName: string
  pluginColor: string
  documentId: string
  documentName: string

  // Event type (used for lane assignment)
  eventType: EventType

  // Progress tracking
  progress: number
  progressMessage: string

  // Status
  status: JobStatus

  // Timing
  startedAt: Date
  endedAt?: Date
  duration?: number // Calculated in ms

  // Layout (computed)
  laneIndex: number // Which sub-row (0, 1, 2...)
  sublaneType: string // "started", "progress", "completed", "failed"

  // Error
  error?: string
}

// Sub-lane within a plugin section
export interface SubLane {
  type: string // "started", "progress", "completed", "failed"
  label: string // Display name
  events: TimelineEvent[]
  rows: number // Number of stacked rows needed
  height: number // Computed: rows * ROW_HEIGHT
  isVisible: boolean // Has events in current time window
}

// Plugin section configuration
export interface PluginSection {
  pluginName: string
  pluginColor: string
  isCollapsed: boolean
  sublanes: SubLane[]
  totalHeight: number // Computed based on sublanes
}

// Timeline viewport state
export interface TimelineViewport {
  startTime: number // Unix timestamp of left edge
  endTime: number // Unix timestamp of right edge
  duration: number // Window size in ms (default 600000 = 10 min)
  pixelsPerMs: number // Zoom level
  width: number // Container width in px
}

// Filter state
export interface TimelineFilters {
  plugins: Set<string> // Enabled plugin names (empty = all)
  eventTypes: Set<EventType> // Enabled event types
  statuses: Set<JobStatus> // Enabled statuses
}

// Selected event for details panel
export interface SelectedEvent {
  event: TimelineEvent
  position: { x: number; y: number } // Screen position for panel
}

// Helper function to convert TimelineJob to TimelineEvent
export function jobToEvent(job: TimelineJob, eventType: EventType): TimelineEvent {
  return {
    id: `${job.id}-${eventType}`,
    jobId: job.id,
    pluginName: job.pluginName,
    pluginColor: job.pluginColor,
    documentId: job.documentId,
    documentName: job.documentName,
    eventType,
    progress: job.progress,
    progressMessage: job.progressMessage,
    status: job.status,
    startedAt: job.startedAt,
    endedAt: job.endedAt,
    duration: job.endedAt
      ? job.endedAt.getTime() - job.startedAt.getTime()
      : undefined,
    laneIndex: 0, // Will be computed by layout algorithm
    sublaneType: eventType.split('.')[1], // "started", "progress", "completed", "failed"
    error: job.error,
  }
}

// Helper to format sublane labels
export function formatSublaneLabel(eventType: string): string {
  const typeMap: Record<string, string> = {
    'job.started': 'Starting',
    'job.progress': 'Processing',
    'job.completed': 'Completed',
    'job.failed': 'Failed',
  }
  return typeMap[eventType] || eventType
}
