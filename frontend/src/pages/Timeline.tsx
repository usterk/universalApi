import { useRef, useEffect, useMemo } from 'react'
import { Header } from '@/components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useTimelineEvents } from '@/core/contexts/SSEContext'
import type { TimelineJob } from '@/core/hooks/useSSE'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/core/api/client'

const TIMELINE_WIDTH = 1200
const ROW_HEIGHT = 40
const PIXELS_PER_SECOND = 4
const TIMELINE_DURATION = 300 // 5 minutes in seconds

function TimelineRow({
  pluginName,
  pluginColor,
  jobs,
  now,
}: {
  pluginName: string
  pluginColor: string
  jobs: TimelineJob[]
  now: number
}) {
  return (
    <div className="flex items-center h-10 border-b">
      <div className="w-40 px-3 text-sm font-medium truncate flex items-center gap-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: pluginColor }}
        />
        {pluginName}
      </div>
      <div className="flex-1 relative h-full">
        {jobs.map((job) => {
          const startOffset = Math.max(
            0,
            (now - job.startedAt.getTime()) / 1000
          )
          const endOffset = job.endedAt
            ? (now - job.endedAt.getTime()) / 1000
            : 0

          const left = Math.max(
            0,
            TIMELINE_WIDTH - startOffset * PIXELS_PER_SECOND
          )
          const right = TIMELINE_WIDTH - endOffset * PIXELS_PER_SECOND
          const width = Math.max(8, right - left)

          if (left > TIMELINE_WIDTH) return null

          return (
            <Tooltip key={job.id}>
              <TooltipTrigger asChild>
                <div
                  className="absolute top-1/2 -translate-y-1/2 h-6 rounded cursor-pointer transition-opacity hover:opacity-80"
                  style={{
                    left: `${left}px`,
                    width: `${width}px`,
                    backgroundColor:
                      job.status === 'failed'
                        ? '#EF4444'
                        : job.status === 'completed'
                        ? pluginColor
                        : `${pluginColor}99`,
                  }}
                />
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="space-y-1">
                  <p className="font-medium">{job.documentName}</p>
                  <p className="text-xs text-muted-foreground">
                    {job.progressMessage}
                  </p>
                  <div className="flex gap-2 text-xs">
                    <Badge variant="secondary">{job.progress}%</Badge>
                    <Badge
                      variant={
                        job.status === 'completed'
                          ? 'default'
                          : job.status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {job.status}
                    </Badge>
                  </div>
                  {job.error && (
                    <p className="text-xs text-destructive">{job.error}</p>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          )
        })}
      </div>
    </div>
  )
}

function TimelineAxis({ now }: { now: number }) {
  const ticks = useMemo(() => {
    const result = []
    for (let i = 0; i <= TIMELINE_DURATION; i += 30) {
      result.push({
        offset: i,
        label:
          i === 0
            ? 'Now'
            : i < 60
            ? `${i}s ago`
            : `${Math.floor(i / 60)}m ago`,
      })
    }
    return result
  }, [])

  return (
    <div className="flex items-center h-8 border-t bg-muted/50">
      <div className="w-40" />
      <div className="flex-1 relative">
        {ticks.map((tick) => (
          <div
            key={tick.offset}
            className="absolute text-xs text-muted-foreground"
            style={{
              left: `${TIMELINE_WIDTH - tick.offset * PIXELS_PER_SECOND}px`,
              transform: 'translateX(-50%)',
            }}
          >
            {tick.label}
          </div>
        ))}
      </div>
    </div>
  )
}

export function Timeline() {
  const { isConnected, jobs, recentJobs } = useTimelineEvents()
  const nowRef = useRef(Date.now())

  // Update now every second
  useEffect(() => {
    const interval = setInterval(() => {
      nowRef.current = Date.now()
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  // Get plugins for colors
  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => api.getPlugins(),
  })

  // Group jobs by plugin
  const jobsByPlugin = useMemo(() => {
    const grouped = new Map<string, TimelineJob[]>()
    const pluginColors = new Map<string, string>()

    plugins?.forEach((p) => {
      pluginColors.set(p.name, p.color)
      grouped.set(p.name, [])
    })

    recentJobs.forEach((job) => {
      const existing = grouped.get(job.pluginName) || []
      grouped.set(job.pluginName, [...existing, job])
      if (!pluginColors.has(job.pluginName)) {
        pluginColors.set(job.pluginName, job.pluginColor)
      }
    })

    return Array.from(grouped.entries())
      .filter(([, jobs]) => jobs.length > 0 || plugins?.some((p) => p.name === jobs[0]?.pluginName && p.is_enabled))
      .map(([name, jobs]) => ({
        name,
        color: pluginColors.get(name) || '#6366F1',
        jobs,
      }))
  }, [recentJobs, plugins])

  return (
    <div className="flex flex-col h-full">
      <Header title="Timeline" />

      <div className="p-6 space-y-6 flex-1">
        {/* Connection Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm">
              {isConnected ? 'Real-time updates active' : 'Reconnecting...'}
            </span>
          </div>
          <Badge variant="secondary">
            {jobs.size} tracked job{jobs.size !== 1 ? 's' : ''}
          </Badge>
        </div>

        {/* Timeline Visualization */}
        <Card>
          <CardHeader>
            <CardTitle>Processing Timeline</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="w-full" style={{ width: TIMELINE_WIDTH + 160 }}>
              <div className="min-w-fit">
                {/* Timeline rows */}
                {jobsByPlugin.length > 0 ? (
                  jobsByPlugin.map(({ name, color, jobs }) => (
                    <TimelineRow
                      key={name}
                      pluginName={name}
                      pluginColor={color}
                      jobs={jobs}
                      now={nowRef.current}
                    />
                  ))
                ) : (
                  <div className="flex items-center justify-center h-32 text-muted-foreground">
                    No processing activity yet
                  </div>
                )}

                {/* Time axis */}
                <TimelineAxis now={nowRef.current} />
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Legend */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Legend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {plugins?.map((plugin) => (
                <div key={plugin.name} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: plugin.color }}
                  />
                  <span className="text-sm">{plugin.display_name}</span>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span className="text-sm">Failed</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
