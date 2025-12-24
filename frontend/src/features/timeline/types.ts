// Timeline feature TypeScript type definitions

import type { TimelineJob } from '@/core/hooks/useSSE'

// Event types from SSE
export type EventType =
  | 'job.started'
  | 'job.progress'
  | 'job.completed'
  | 'job.failed'
  | 'system.health_check.started'
  | 'system.health_check.completed'
  | 'system.health_check.failed'
  | 'document.created'
  | 'document.updated'
  | 'document.deleted'

// Job status
export type JobStatus = 'running' | 'completed' | 'failed'

// System activity (for health checks, maintenance, etc.)
export interface SystemActivity {
  id: string
  activityType: string // "health_check", "maintenance", etc.
  activityName: string
  activityColor: string
  status: JobStatus
  progress: number
  progressMessage: string
  startedAt: Date
  endedAt?: Date
  error?: string
  details?: Record<string, unknown>
}

// Document event (for uploads, deletions, etc.)
export interface DocumentEvent {
  id: string
  documentId: string
  documentName: string
  documentType: string
  contentType: string
  sizeBytes: number
  eventType: 'document.created' | 'document.updated' | 'document.deleted'
  timestamp: Date
  sourceId?: string
  pluginName: string
  pluginColor: string
}

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

// Plugin section configuration (simplified - no sublanes)
export interface PluginSection {
  pluginName: string
  pluginColor: string
  isCollapsed: boolean
  events: TimelineEvent[] // Direct events instead of sublanes
  documentEvents?: DocumentEvent[] // Document events (for Documents section)
  rows: number // Number of stacked rows needed for overlap handling
  totalHeight: number // Computed based on rows
  isSystem?: boolean // Flag to identify system section (health checks, etc.)
  isDocuments?: boolean // Flag to identify Documents section
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
export function jobToEvent(job: TimelineJob): TimelineEvent {
  // Infer event type from job status
  let eventType: EventType
  if (job.status === 'failed') {
    eventType = 'job.failed'
  } else if (job.status === 'completed') {
    eventType = 'job.completed'
  } else if (job.progress > 0) {
    eventType = 'job.progress'
  } else {
    eventType = 'job.started'
  }

  return {
    id: job.id, // Use job ID directly (no suffix needed without sublanes)
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

// Helper function to convert SystemActivity to TimelineEvent
export function systemActivityToEvent(activity: SystemActivity): TimelineEvent {
  // Infer event type from activity status
  let eventType: EventType
  if (activity.status === 'failed') {
    eventType = 'system.health_check.failed'
  } else if (activity.status === 'completed') {
    eventType = 'system.health_check.completed'
  } else {
    eventType = 'system.health_check.started'
  }

  return {
    id: activity.id,
    jobId: activity.id,
    pluginName: 'System',
    pluginColor: activity.activityColor,
    documentId: activity.activityType,
    documentName: activity.activityName,
    eventType,
    progress: activity.progress,
    progressMessage: activity.progressMessage,
    status: activity.status,
    startedAt: activity.startedAt,
    endedAt: activity.endedAt,
    duration: activity.endedAt
      ? activity.endedAt.getTime() - activity.startedAt.getTime()
      : undefined,
    laneIndex: 0, // Will be computed by layout algorithm
    sublaneType: activity.status,
    error: activity.error,
  }
}
