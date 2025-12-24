import { useState } from 'react'
import { ChevronRight, ChevronDown } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useDocumentTree } from './hooks/useDocumentTree'
import { formatFileSize } from '@/pages/Documents'
import { format } from 'date-fns'
import type { DocumentTreeNode } from '@/core/api/client'
import type { DocumentFilters } from './hooks/useDocumentFilters'

interface TreeNodeProps {
  node: DocumentTreeNode
  level: number
  onSelect: (id: string) => void
}

function TreeNode({ node, level, onSelect }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(false)
  const hasChildren = node.children.length > 0

  const filename = (node.properties?.original_filename as string) || node.filepath

  return (
    <div>
      <div
        className="flex items-center gap-2 py-2 px-3 hover:bg-muted/50 cursor-pointer rounded"
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={() => onSelect(node.id)}
        onDoubleClick={() => hasChildren && setExpanded(!expanded)}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setExpanded(!expanded)
            }}
            className="p-0 h-4 w-4"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        )}
        {!hasChildren && <div className="w-4" />}

        <Badge variant="secondary">{node.type_display_name}</Badge>
        <span className="flex-1 truncate">{filename}</span>
        <span className="text-sm text-muted-foreground">
          {formatFileSize(node.size_bytes)}
        </span>
        <span className="text-xs text-muted-foreground">
          {format(new Date(node.created_at), 'PP')}
        </span>
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface DocumentTreeViewProps {
  page: number
  pageSize: number
  filters: DocumentFilters
  onSelectDocument: (id: string) => void
  onPageChange: (page: number) => void
}

export function DocumentTreeView({
  page,
  pageSize,
  filters,
  onSelectDocument,
  onPageChange,
}: DocumentTreeViewProps) {
  const { data, isLoading, error } = useDocumentTree(page, pageSize, filters)

  if (isLoading) return <div className="p-4">Loading...</div>
  if (error) return <div className="p-4 text-destructive">Error loading documents</div>
  if (!data?.items.length) {
    return <div className="p-4 text-muted-foreground">No documents found</div>
  }

  return (
    <div className="space-y-4">
      <div className="border rounded-lg">
        {data.items.map((node) => (
          <TreeNode key={node.id} node={node} level={0} onSelect={onSelectDocument} />
        ))}
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </Button>
          <span className="flex items-center px-4 text-sm text-muted-foreground">
            Page {page} of {Math.ceil(data.total / data.page_size)}
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(data.total / data.page_size)}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
