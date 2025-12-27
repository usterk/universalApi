import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SourceWorkflowsTab } from '@/features/sources/components/SourceWorkflowsTab'
import { api } from '@/core/api/client'

function SourceOverview({ sourceId }: { sourceId: string }) {
  const { data: source } = useQuery({
    queryKey: ['sources', sourceId],
    queryFn: () => api.getSource(sourceId),
  })

  if (!source) return null

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Source Information</CardTitle>
          <CardDescription>Basic details about this data source</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p className="text-lg font-semibold">{source.name}</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Status</p>
              <Badge variant={source.is_active ? 'default' : 'secondary'}>
                {source.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">API Key Prefix</p>
              <code className="rounded bg-muted px-2 py-1 text-sm">
                {source.api_key_prefix}...
              </code>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Created</p>
              <p>{new Date(source.created_at).toLocaleDateString()}</p>
            </div>
          </div>
          {source.description && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Description</p>
              <p className="text-sm">{source.description}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function SourceDocuments({ sourceId }: { sourceId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['documents', { sourceId }],
    queryFn: () => api.getDocuments(1, 50, undefined, sourceId),
  })

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>Files uploaded from this source</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center text-muted-foreground py-4">Loading documents...</p>
          ) : !data?.items?.length ? (
            <p className="text-center text-muted-foreground py-4">No documents yet</p>
          ) : (
            <div className="space-y-2">
              {data.items.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p className="font-medium">
                      {doc.properties.original_filename as string || doc.filepath}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {doc.type_display_name} • {(doc.size_bytes / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: source, isLoading } = useQuery({
    queryKey: ['sources', id],
    queryFn: () => api.getSource(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex flex-col">
        <Header title="Source Details" />
        <div className="flex items-center justify-center p-8">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!source || !id) {
    return (
      <div className="flex flex-col">
        <Header title="Source Not Found" />
        <div className="flex items-center justify-center p-8">
          <p className="text-muted-foreground">Source not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      <Header title={source.name}>
        <Button variant="ghost" size="sm" onClick={() => navigate('/sources')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Sources
        </Button>
      </Header>

      <div className="p-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="workflows">Workflows</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <SourceOverview sourceId={id} />
          </TabsContent>

          <TabsContent value="documents" className="mt-6">
            <SourceDocuments sourceId={id} />
          </TabsContent>

          <TabsContent value="workflows" className="mt-6">
            <SourceWorkflowsTab sourceId={id} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
