import { useQuery } from '@tanstack/react-query'
import {
  FileAudio,
  Database,
  Upload,
  Plug,
  Activity,
  TrendingUp,
} from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { api } from '@/core/api/client'
import { useTimelineEvents } from '@/core/contexts/SSEContext'
import type { TimelineJob } from '@/core/hooks/useSSE'

function StatCard({
  title,
  value,
  icon: Icon,
  description,
}: {
  title: string
  value: string | number
  icon: React.ElementType
  description?: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  )
}

function ActiveJobCard({ job }: { job: TimelineJob }) {
  return (
    <div className="flex items-center gap-4 rounded-lg border p-4">
      <div
        className="h-3 w-3 rounded-full"
        style={{ backgroundColor: job.pluginColor }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{job.documentName}</p>
        <p className="text-xs text-muted-foreground">{job.pluginName}</p>
      </div>
      <div className="flex items-center gap-2">
        <Progress value={job.progress} className="w-24" />
        <span className="text-sm text-muted-foreground w-10">
          {job.progress}%
        </span>
      </div>
    </div>
  )
}

export function Dashboard() {
  const { activeJobs, recentJobs } = useTimelineEvents()

  const { data: sources } = useQuery({
    queryKey: ['sources'],
    queryFn: () => api.getSources(1, 1),
  })

  const { data: documents } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments(1, 1),
  })

  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => api.getPlugins(),
  })

  const enabledPlugins = plugins?.filter((p) => p.is_enabled).length || 0
  const completedJobs = recentJobs.filter((j) => j.status === 'completed').length
  const failedJobs = recentJobs.filter((j) => j.status === 'failed').length

  return (
    <div className="flex flex-col">
      <Header title="Dashboard" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Documents"
            value={documents?.total || 0}
            icon={Database}
            description="All uploaded documents"
          />
          <StatCard
            title="Active Sources"
            value={sources?.total || 0}
            icon={Upload}
            description="External data sources"
          />
          <StatCard
            title="Enabled Plugins"
            value={enabledPlugins}
            icon={Plug}
            description={`${plugins?.length || 0} total plugins`}
          />
          <StatCard
            title="Processing Rate"
            value={`${completedJobs}/${completedJobs + failedJobs}`}
            icon={TrendingUp}
            description="Recent success rate"
          />
        </div>

        {/* Active Jobs */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Active Processing Jobs
            </CardTitle>
          </CardHeader>
          <CardContent>
            {activeJobs.length > 0 ? (
              <div className="space-y-3">
                {activeJobs.map((job) => (
                  <ActiveJobCard key={job.id} job={job} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No active jobs at the moment
              </p>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileAudio className="h-5 w-5" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            {recentJobs.length > 0 ? (
              <div className="space-y-3">
                {recentJobs.slice(0, 10).map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: job.pluginColor }}
                      />
                      <div>
                        <p className="text-sm font-medium">{job.documentName}</p>
                        <p className="text-xs text-muted-foreground">
                          {job.pluginName}
                        </p>
                      </div>
                    </div>
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
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No recent activity
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
