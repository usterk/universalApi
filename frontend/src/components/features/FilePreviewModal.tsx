import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Download, X } from 'lucide-react'
import { api, type Document } from '@/core/api/client'
import { FilePreview } from './FilePreview'

interface FilePreviewModalProps {
  document: Document | null
  open: boolean
  onClose: () => void
}

export function FilePreviewModal({ document, open, onClose }: FilePreviewModalProps) {
  if (!document) return null

  const handleDownload = async () => {
    try {
      const filename = (document.properties?.original_filename as string) || 'download'
      await api.downloadFile(document.id, filename)
    } catch (err) {
      console.error('Failed to download file', err)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>
              {(document.properties?.original_filename as string) || 'File Preview'}
            </DialogTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <DialogDescription className="sr-only">
            Preview of {(document.properties?.original_filename as string) || 'file'}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1">
          <FilePreview document={document} maxHeight="calc(90vh - 150px)" />
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
