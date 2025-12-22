import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import {
  FileAudio,
  FileVideo,
  FileImage,
  FileText,
  File,
  Trash2,
  ChevronRight,
  Upload,
} from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { api, type Document } from '@/core/api/client'
import { log } from '@/core/utils/logger'

function getFileIcon(contentType: string) {
  if (contentType.startsWith('audio/')) return FileAudio
  if (contentType.startsWith('video/')) return FileVideo
  if (contentType.startsWith('image/')) return FileImage
  if (contentType.startsWith('text/') || contentType.includes('json')) return FileText
  return File
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

function UploadDialog() {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [progress, setProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const queryClient = useQueryClient()

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    try {
      await api.uploadFile(file, undefined, setProgress)
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setOpen(false)
      setFile(null)
      setProgress(0)
    } catch (error) {
      log.error('upload_failed', error, { filename: file.name, size: file.size })
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Upload className="mr-2 h-4 w-4" />
          Upload File
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload File</DialogTitle>
          <DialogDescription>
            Upload a file for processing
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <Input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          {file && (
            <div className="text-sm">
              <p>
                <strong>File:</strong> {file.name}
              </p>
              <p>
                <strong>Size:</strong> {formatFileSize(file.size)}
              </p>
              <p>
                <strong>Type:</strong> {file.type || 'Unknown'}
              </p>
            </div>
          )}
          {isUploading && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-sm text-center text-muted-foreground">
                {progress}%
              </p>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file || isUploading}>
            Upload
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DocumentCard({ document }: { document: Document }) {
  const queryClient = useQueryClient()
  const [expanded, setExpanded] = useState(false)
  const Icon = getFileIcon(document.content_type)

  const { data: children } = useQuery({
    queryKey: ['document-children', document.id],
    queryFn: () => api.getDocumentChildren(document.id),
    enabled: expanded,
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteDocument(document.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const originalFilename =
    (document.properties?.original_filename as string) || document.filepath.split('/').pop()

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
              <Icon className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-base">{originalFilename}</CardTitle>
              <CardDescription>
                {document.type_name} - {formatFileSize(document.size_bytes)}
              </CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => deleteMutation.mutate()}
          >
            <Trash2 className="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Content Type</span>
            <span>{document.content_type}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Storage</span>
            <Badge variant="outline">{document.storage_plugin}</Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{format(new Date(document.created_at), 'PPp')}</span>
          </div>
          {document.source_id && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Source</span>
              <span className="text-xs font-mono">{document.source_id.slice(0, 8)}...</span>
            </div>
          )}
        </div>

        {/* Children toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="mt-3 w-full justify-start"
          onClick={() => setExpanded(!expanded)}
        >
          <ChevronRight
            className={`mr-2 h-4 w-4 transition-transform ${expanded ? 'rotate-90' : ''}`}
          />
          Generated Documents
        </Button>

        {expanded && children && children.length > 0 && (
          <ScrollArea className="mt-2 max-h-40">
            <div className="space-y-2 pl-6">
              {children.map((child) => (
                <div
                  key={child.id}
                  className="flex items-center justify-between rounded border p-2 text-sm"
                >
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{child.type_name}</Badge>
                    <span className="text-muted-foreground">
                      {formatFileSize(child.size_bytes)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

export function Documents() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['documents', page],
    queryFn: () => api.getDocuments(page, 20),
  })

  return (
    <div className="flex flex-col">
      <Header title="Documents" />

      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">All Documents</h2>
            <p className="text-sm text-muted-foreground">
              Browse and manage uploaded documents
            </p>
          </div>
          <UploadDialog />
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading...</div>
        ) : !data?.items?.length ? (
          <Card className="py-8">
            <CardContent className="text-center">
              <p className="text-muted-foreground mb-4">No documents yet</p>
              <UploadDialog />
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data?.items.map((doc) => (
                <DocumentCard key={doc.id} document={doc} />
              ))}
            </div>

            {/* Pagination */}
            {data && data.total > data.page_size && (
              <div className="flex justify-center gap-2">
                <Button
                  variant="outline"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4 text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(data.total / data.page_size)}
                </span>
                <Button
                  variant="outline"
                  disabled={page >= Math.ceil(data.total / data.page_size)}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
