import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useDocumentDetails } from './hooks/useDocumentDetails'
import { formatFileSize } from '@/pages/Documents'
import { format } from 'date-fns'
import { FilePreview } from '@/components/features/FilePreview'

interface DocumentDetailsProps {
  documentId: string | null
  open: boolean
  onClose: () => void
}

export function DocumentDetails({ documentId, open, onClose }: DocumentDetailsProps) {
  const { data, isLoading } = useDocumentDetails(documentId)

  if (!documentId) return null

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-[600px] sm:max-w-[600px]">
        <SheetHeader>
          <SheetTitle>Document Details</SheetTitle>
        </SheetHeader>

        {isLoading && <div className="p-4">Loading...</div>}

        {data && (
          <Tabs defaultValue="overview" className="mt-4">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="processing">Processing</TabsTrigger>
              <TabsTrigger value="events">Events</TabsTrigger>
              <TabsTrigger value="relationships">Relations</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <ScrollArea className="h-[calc(100vh-200px)] mt-4">
              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                <div className="space-y-2">
                  <h4 className="font-semibold">Basic Info</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-muted-foreground">ID:</div>
                    <div className="font-mono text-xs">{data.document.id}</div>

                    <div className="text-muted-foreground">Filename:</div>
                    <div>{(data.document.properties?.original_filename as string) || 'N/A'}</div>

                    <div className="text-muted-foreground">Type:</div>
                    <Badge variant="secondary">{data.document.type_name}</Badge>

                    <div className="text-muted-foreground">Content Type:</div>
                    <div>{data.document.content_type}</div>

                    <div className="text-muted-foreground">Size:</div>
                    <div>{formatFileSize(data.document.size_bytes)}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-semibold">Storage</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-muted-foreground">Plugin:</div>
                    <div>{data.document.storage_plugin}</div>

                    <div className="text-muted-foreground">Filepath:</div>
                    <div className="font-mono text-xs truncate">{data.document.filepath}</div>

                    <div className="text-muted-foreground">Checksum:</div>
                    <div className="font-mono text-xs truncate">{data.document.checksum}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-semibold">Ownership</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-muted-foreground">Owner ID:</div>
                    <div className="font-mono text-xs">{data.document.owner_id}</div>

                    <div className="text-muted-foreground">Source ID:</div>
                    <div className="font-mono text-xs">{data.document.source_id || 'N/A'}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-semibold">Timestamps</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-muted-foreground">Created:</div>
                    <div>{format(new Date(data.document.created_at), 'PPpp')}</div>

                    <div className="text-muted-foreground">Updated:</div>
                    <div>{format(new Date(data.document.updated_at), 'PPpp')}</div>
                  </div>
                </div>

                {/* Properties (JSONB) */}
                <div className="space-y-2">
                  <h4 className="font-semibold">Properties</h4>
                  <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                    {JSON.stringify(data.document.properties, null, 2)}
                  </pre>
                </div>
              </TabsContent>

              {/* Processing Jobs Tab */}
              <TabsContent value="processing" className="space-y-2">
                {data.processing_jobs.length === 0 ? (
                  <p className="text-muted-foreground">No processing jobs</p>
                ) : (
                  data.processing_jobs.map((job) => (
                    <div key={job.id} className="border rounded p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{job.plugin_name}</span>
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
                      {job.progress_message && (
                        <p className="text-sm text-muted-foreground">{job.progress_message}</p>
                      )}
                      {job.error_message && (
                        <p className="text-sm text-destructive">{job.error_message}</p>
                      )}
                      <div className="text-xs text-muted-foreground">
                        {format(new Date(job.created_at), 'PPp')}
                      </div>
                    </div>
                  ))
                )}
              </TabsContent>

              {/* System Events Tab */}
              <TabsContent value="events" className="space-y-2">
                {data.system_events.length === 0 ? (
                  <p className="text-muted-foreground">No events</p>
                ) : (
                  data.system_events.map((event) => (
                    <div key={event.id} className="border rounded p-3 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-mono">{event.event_type}</span>
                        <Badge variant="outline">{event.severity}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">From: {event.source}</p>
                      <p className="text-xs text-muted-foreground">
                        {format(new Date(event.created_at), 'PPp')}
                      </p>
                    </div>
                  ))
                )}
              </TabsContent>

              {/* Relationships Tab */}
              <TabsContent value="relationships" className="space-y-4">
                {/* Parent */}
                <div className="space-y-2">
                  <h4 className="font-semibold">Parent Document</h4>
                  {data.parent ? (
                    <div className="border rounded p-3">
                      <Badge variant="secondary">{data.parent.type_name}</Badge>
                      <p className="text-sm mt-1">
                        {(data.parent.properties?.original_filename as string) || 'N/A'}
                      </p>
                    </div>
                  ) : (
                    <p className="text-muted-foreground">No parent (root document)</p>
                  )}
                </div>

                {/* Children */}
                <div className="space-y-2">
                  <h4 className="font-semibold">Child Documents</h4>
                  {data.children.length === 0 ? (
                    <p className="text-muted-foreground">No children</p>
                  ) : (
                    data.children.map((child) => (
                      <div key={child.id} className="border rounded p-3">
                        <Badge variant="secondary">{child.type_name}</Badge>
                        <p className="text-sm mt-1">
                          {(child.properties?.original_filename as string) || 'N/A'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(child.size_bytes)}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>

              {/* Preview Tab */}
              <TabsContent value="preview" className="space-y-2">
                <FilePreview
                  document={data.document}
                  maxHeight="calc(100vh - 250px)"
                  className="rounded-lg"
                />
              </TabsContent>
            </ScrollArea>
          </Tabs>
        )}
      </SheetContent>
    </Sheet>
  )
}
