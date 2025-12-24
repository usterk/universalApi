import { ScrollArea } from '@/components/ui/scroll-area'
import { FileText, ChevronRight } from 'lucide-react'
import type { Document } from '@/core/api/client'
import { cn } from '@/lib/utils'

interface ColumnProps {
  documents: Document[]
  selectedId: string | null
  onSelect: (document: Document) => void
  onNavigate: (document: Document) => void
  isLoading?: boolean
}

export function Column({ documents, selectedId, onSelect, onNavigate, isLoading }: ColumnProps) {
  if (isLoading) {
    return (
      <div className="w-[350px] border-r bg-background flex-shrink-0">
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
          Loading...
        </div>
      </div>
    )
  }

  if (documents.length === 0) {
    return (
      <div className="w-[350px] border-r bg-background flex-shrink-0">
        <div className="flex items-center justify-center h-full text-muted-foreground text-sm p-4 text-center">
          No documents
        </div>
      </div>
    )
  }

  return (
    <div className="w-[350px] border-r bg-background flex-shrink-0">
      <ScrollArea className="h-full">
        <div className="py-1">
          {documents.map((doc) => (
            <button
              key={doc.id}
              className={cn(
                'w-full px-3 py-2 text-left text-sm hover:bg-muted/50 transition-colors flex items-center gap-2',
                selectedId === doc.id && 'bg-primary/10 hover:bg-primary/15'
              )}
              onClick={() => onSelect(doc)}
              onDoubleClick={() => onNavigate(doc)}
            >
              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <span className="truncate flex-1">
                {(doc.properties?.original_filename as string) || doc.filepath}
              </span>
              <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0 opacity-0 group-hover:opacity-100" />
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
