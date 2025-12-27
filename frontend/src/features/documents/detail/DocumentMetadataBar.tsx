import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Download } from 'lucide-react'
import { format } from 'date-fns'
import { formatFileSize } from '@/pages/Documents'
import { api, type Document } from '@/core/api/client'

interface DocumentMetadataBarProps {
  document?: Document
}

export function DocumentMetadataBar({ document }: DocumentMetadataBarProps) {
  if (!document) return null

  const filename = (document.properties?.original_filename as string) || document.filepath

  const handleDownload = () => {
    api.downloadFile(document.id, filename)
  }

  return (
    <div className="flex items-center gap-4 border-b px-6 py-4">
      <Badge variant="outline">{document.type_display_name}</Badge>
      <span className="text-sm text-muted-foreground">
        {formatFileSize(document.size_bytes)}
      </span>
      <span className="text-sm text-muted-foreground">
        {format(new Date(document.created_at), 'PPp')}
      </span>
      <div className="ml-auto">
        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="mr-2 h-4 w-4" />
          Download
        </Button>
      </div>
    </div>
  )
}
