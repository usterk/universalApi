import { Badge } from '@/components/ui/badge'
import { format } from 'date-fns'
import { formatFileSize } from '@/pages/Documents'
import { type Document } from '@/core/api/client'

interface DocumentOverviewProps {
  document?: Document
}

export function DocumentOverview({ document }: DocumentOverviewProps) {
  if (!document) return null

  return (
    <div className="space-y-6 p-6">
      {/* Basic Info */}
      <div className="space-y-2">
        <h4 className="font-semibold">Basic Info</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-muted-foreground">ID:</div>
          <div className="font-mono text-xs">{document.id}</div>

          <div className="text-muted-foreground">Filename:</div>
          <div>{(document.properties?.original_filename as string) || 'N/A'}</div>

          <div className="text-muted-foreground">Type:</div>
          <Badge variant="secondary">{document.type_name}</Badge>

          <div className="text-muted-foreground">Content Type:</div>
          <div>{document.content_type}</div>

          <div className="text-muted-foreground">Size:</div>
          <div>{formatFileSize(document.size_bytes)}</div>
        </div>
      </div>

      {/* Storage */}
      <div className="space-y-2">
        <h4 className="font-semibold">Storage</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-muted-foreground">Plugin:</div>
          <div>{document.storage_plugin}</div>

          <div className="text-muted-foreground">Filepath:</div>
          <div className="truncate font-mono text-xs">{document.filepath}</div>

          <div className="text-muted-foreground">Checksum:</div>
          <div className="truncate font-mono text-xs">{document.checksum}</div>
        </div>
      </div>

      {/* Ownership */}
      <div className="space-y-2">
        <h4 className="font-semibold">Ownership</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-muted-foreground">Owner ID:</div>
          <div className="font-mono text-xs">{document.owner_id}</div>

          <div className="text-muted-foreground">Source ID:</div>
          <div className="font-mono text-xs">{document.source_id || 'N/A'}</div>
        </div>
      </div>

      {/* Timestamps */}
      <div className="space-y-2">
        <h4 className="font-semibold">Timestamps</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-muted-foreground">Created:</div>
          <div>{format(new Date(document.created_at), 'PPpp')}</div>

          <div className="text-muted-foreground">Updated:</div>
          <div>{format(new Date(document.updated_at), 'PPpp')}</div>
        </div>
      </div>

      {/* Properties (JSONB) */}
      <div className="space-y-2">
        <h4 className="font-semibold">Properties</h4>
        <pre className="overflow-auto rounded bg-muted p-2 text-xs">
          {JSON.stringify(document.properties, null, 2)}
        </pre>
      </div>
    </div>
  )
}
