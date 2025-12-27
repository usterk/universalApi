import { X, FileText, Calendar, HardDrive, ExternalLink } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { FilePreview } from '@/components/features/FilePreview'
import type { Document } from '@/core/api/client'
import { cn } from '@/lib/utils'

interface PreviewPanelProps {
  document: Document | null
  isOpen: boolean
  onClose: () => void
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function PreviewPanel({ document, isOpen, onClose }: PreviewPanelProps) {
  const navigate = useNavigate()

  return (
    <div
      className={cn(
        'fixed right-0 top-0 h-screen w-[400px] bg-background border-l shadow-lg z-50 transition-transform duration-300 ease-in-out',
        isOpen ? 'translate-x-0' : 'translate-x-full'
      )}
    >
      {document && (
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-semibold truncate flex-1">
              {(document.properties?.original_filename as string) || 'Preview'}
            </h3>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Preview Content */}
          <div className="flex-1 overflow-hidden p-4">
            <FilePreview
              document={document}
              maxHeight="calc(100vh - 350px)"
              className="mb-4"
            />
          </div>

          {/* Metadata */}
          <div className="border-t p-4 space-y-3">
            <div className="flex items-start gap-2 text-sm">
              <FileText className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1">
                <div className="text-muted-foreground text-xs">Type</div>
                <div className="font-medium">{document.type_display_name}</div>
              </div>
            </div>

            <div className="flex items-start gap-2 text-sm">
              <HardDrive className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1">
                <div className="text-muted-foreground text-xs">Size</div>
                <div className="font-medium">{formatFileSize(document.size_bytes)}</div>
              </div>
            </div>

            <div className="flex items-start gap-2 text-sm">
              <Calendar className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
              <div className="flex-1">
                <div className="text-muted-foreground text-xs">Created</div>
                <div className="font-medium">{formatDate(document.created_at)}</div>
              </div>
            </div>

            {/* View Details Button */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                navigate(`/documents/${document.id}`)
                onClose()
              }}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              View Full Details
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
