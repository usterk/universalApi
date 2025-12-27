import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatFileSize } from '@/pages/Documents'
import { type Document } from '@/core/api/client'

interface RelatedDocumentsProps {
  parent?: Document | null
  children?: Document[]
}

export function RelatedDocuments({ parent, children }: RelatedDocumentsProps) {
  const navigate = useNavigate()

  return (
    <div className="space-y-6 p-6">
      {/* Parent Document */}
      {parent && (
        <div>
          <h3 className="mb-2 text-sm font-medium">Parent Document</h3>
          <Card
            className="cursor-pointer transition-colors hover:bg-accent"
            onClick={() => navigate(`/documents/${parent.id}`)}
          >
            <CardContent className="flex items-center gap-3 p-4">
              <Badge variant="outline">{parent.type_display_name}</Badge>
              <span className="font-medium">
                {(parent.properties?.original_filename as string) || parent.filepath}
              </span>
              <span className="ml-auto text-sm text-muted-foreground">
                {formatFileSize(parent.size_bytes)}
              </span>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Children Documents */}
      {children && children.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-medium">Generated Documents</h3>
          <div className="space-y-2">
            {children.map((child) => (
              <Card
                key={child.id}
                className="cursor-pointer transition-colors hover:bg-accent"
                onClick={() => navigate(`/documents/${child.id}`)}
              >
                <CardContent className="flex items-center gap-3 p-4">
                  <Badge variant="outline">{child.type_display_name}</Badge>
                  <span className="font-medium">
                    {(child.properties?.original_filename as string) || child.filepath}
                  </span>
                  <span className="ml-auto text-sm text-muted-foreground">
                    {formatFileSize(child.size_bytes)}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!parent && (!children || children.length === 0) && (
        <div className="flex h-full items-center justify-center py-8">
          <div className="text-center text-muted-foreground">No related documents</div>
        </div>
      )}
    </div>
  )
}
