import { useMemo, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { useDocumentDetails } from '@/features/documents/browser/hooks/useDocumentDetails'
import { useTimelineEvents } from '@/core/contexts/SSEContext'
import { DocumentMetadataBar } from '@/features/documents/detail/DocumentMetadataBar'
import { DocumentOverview } from '@/features/documents/detail/DocumentOverview'
import { ProcessingSection } from '@/features/documents/detail/ProcessingSection'
import { RelatedDocuments } from '@/features/documents/detail/RelatedDocuments'
import { FilePreview } from '@/components/features/FilePreview'

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch document details
  const { data, isLoading, error } = useDocumentDetails(id || null)

  // SSE subscription dla live updates
  const { jobs } = useTimelineEvents()
  const documentJobs = useMemo(
    () => Array.from(jobs.values()).filter((j) => j.document_id === id),
    [jobs, id]
  )

  // Auto-refresh gdy job się kończy
  useEffect(() => {
    const completed = documentJobs.find((j) => j.status === 'completed')
    if (completed) {
      queryClient.invalidateQueries({ queryKey: ['document-details', id] })
    }
  }, [documentJobs, id, queryClient])

  if (!id) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">Invalid document ID</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <div className="text-muted-foreground">Document not found</div>
        <Button onClick={() => navigate('/documents')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Documents
        </Button>
      </div>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  const documentName =
    (data.document.properties?.original_filename as string) || data.document.filepath

  return (
    <div className="flex h-full flex-col">
      {/* Header with back button */}
      <Header
        title={
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/documents')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <span>{documentName}</span>
          </div>
        }
      />

      {/* Metadata bar */}
      <DocumentMetadataBar document={data.document} />

      {/* Main content with tabs */}
      <div className="flex-1 overflow-hidden">
        <Tabs defaultValue="preview" className="flex h-full flex-col">
          <div className="border-b px-6">
            <TabsList className="h-12">
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="processing">
                Processing
                {documentJobs.length > 0 && (
                  <span className="ml-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                    {documentJobs.length}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="related">Related</TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-auto">
            <TabsContent value="preview" className="m-0 h-full">
              <div className="p-6">
                <FilePreview document={data.document} maxHeight="calc(100vh - 250px)" />
              </div>
            </TabsContent>

            <TabsContent value="overview" className="m-0">
              <DocumentOverview document={data.document} />
            </TabsContent>

            <TabsContent value="processing" className="m-0">
              <ProcessingSection jobs={documentJobs} events={data.system_events} />
            </TabsContent>

            <TabsContent value="related" className="m-0">
              <RelatedDocuments parent={data.parent} children={data.children} />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  )
}
