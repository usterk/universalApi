import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { format } from 'date-fns'
import { type ProcessingJob, type SystemEventResponse } from '@/core/api/client'

interface ProcessingSectionProps {
  jobs: ProcessingJob[]
  events?: SystemEventResponse[]
}

export function ProcessingSection({ jobs, events }: ProcessingSectionProps) {
  if (jobs.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="text-center text-muted-foreground">No processing jobs</div>
      </div>
    )
  }

  const getStatusVariant = (
    status: string
  ): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'completed':
        return 'default'
      case 'failed':
      case 'cancelled':
        return 'destructive'
      case 'running':
        return 'default'
      default:
        return 'secondary'
    }
  }

  return (
    <div className="space-y-4 p-6">
      {jobs.map((job) => (
        <Card key={job.id}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">{job.plugin_name}</CardTitle>
              <Badge variant={getStatusVariant(job.status)}>{job.status}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Progress bar for running jobs */}
            {job.status === 'running' && (
              <div>
                <Progress value={job.progress} className="mb-2" />
                <p className="text-xs text-muted-foreground">{job.progress}%</p>
              </div>
            )}

            {/* Progress message */}
            {job.progress_message && (
              <p className="text-sm text-muted-foreground">{job.progress_message}</p>
            )}

            {/* Error message */}
            {job.error_message && (
              <Alert variant="destructive">
                <AlertDescription>{job.error_message}</AlertDescription>
              </Alert>
            )}

            {/* Timestamps */}
            <div className="text-xs text-muted-foreground space-y-1">
              <div>Created: {format(new Date(job.created_at), 'PPp')}</div>
              {job.started_at && <div>Started: {format(new Date(job.started_at), 'PPp')}</div>}
              {job.completed_at && (
                <div>Completed: {format(new Date(job.completed_at), 'PPp')}</div>
              )}
            </div>

            {/* Output document link */}
            {job.output_document_id && (
              <div className="text-sm">
                <span className="text-muted-foreground">Output: </span>
                <a
                  href={`/documents/${job.output_document_id}`}
                  className="text-primary hover:underline"
                >
                  View result document
                </a>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
