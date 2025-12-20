import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plug, Power, PowerOff, Settings } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api, type PluginInfo } from '@/core/api/client'

function PluginCard({ plugin }: { plugin: PluginInfo }) {
  const queryClient = useQueryClient()

  const enableMutation = useMutation({
    mutationFn: () => api.enablePlugin(plugin.name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
    },
  })

  const disableMutation = useMutation({
    mutationFn: () => api.disablePlugin(plugin.name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] })
    },
  })

  const toggleEnabled = () => {
    if (plugin.is_enabled) {
      disableMutation.mutate()
    } else {
      enableMutation.mutate()
    }
  }

  return (
    <Card className={!plugin.is_enabled ? 'opacity-60' : undefined}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{ backgroundColor: plugin.color + '20' }}
            >
              <Plug className="h-5 w-5" style={{ color: plugin.color }} />
            </div>
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                {plugin.display_name}
                <Badge variant={plugin.is_enabled ? 'default' : 'secondary'}>
                  {plugin.is_enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </CardTitle>
              <CardDescription>{plugin.description}</CardDescription>
            </div>
          </div>
          <div className="flex gap-1">
            <Button variant="ghost" size="icon">
              <Settings className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleEnabled}
              disabled={enableMutation.isPending || disableMutation.isPending}
            >
              {plugin.is_enabled ? (
                <PowerOff className="h-4 w-4 text-destructive" />
              ) : (
                <Power className="h-4 w-4 text-green-500" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Version</span>
              <p className="font-medium">{plugin.version}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Priority</span>
              <p className="font-medium">{plugin.priority}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Max Concurrent</span>
              <p className="font-medium">{plugin.max_concurrent_jobs}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Output Type</span>
              <p className="font-medium">{plugin.output_type || 'None'}</p>
            </div>
          </div>

          {plugin.input_types.length > 0 && (
            <div>
              <span className="text-sm text-muted-foreground">Input Types</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {plugin.input_types.map((type) => (
                  <Badge key={type} variant="outline">
                    {type}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {plugin.dependencies.length > 0 && (
            <div>
              <span className="text-sm text-muted-foreground">Dependencies</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {plugin.dependencies.map((dep) => (
                  <Badge key={dep} variant="secondary">
                    {dep}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function Plugins() {
  const { data: plugins, isLoading } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => api.getPlugins(),
  })

  // Sort by priority
  const sortedPlugins = plugins?.sort((a, b) => a.priority - b.priority)

  return (
    <div className="flex flex-col">
      <Header title="Plugins" />

      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">Installed Plugins</h2>
          <p className="text-sm text-muted-foreground">
            Manage data processing plugins (sorted by priority)
          </p>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading...</div>
        ) : sortedPlugins?.length === 0 ? (
          <Card className="py-8">
            <CardContent className="text-center">
              <p className="text-muted-foreground">No plugins installed</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {sortedPlugins?.map((plugin) => (
              <PluginCard key={plugin.name} plugin={plugin} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
