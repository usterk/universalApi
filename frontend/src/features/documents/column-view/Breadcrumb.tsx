import { ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { NavigationLevel } from './hooks/useColumnNavigation'

interface BreadcrumbProps {
  path: NavigationLevel[]
  onNavigateBack: (level: number) => void
}

export function Breadcrumb({ path, onNavigateBack }: BreadcrumbProps) {
  return (
    <div className="flex items-center gap-1 px-4 py-2 border-b bg-muted/30 overflow-x-auto">
      {path.map((level, index) => (
        <div key={index} className="flex items-center gap-1 flex-shrink-0">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 hover:bg-muted"
            onClick={() => onNavigateBack(index)}
          >
            <span className="max-w-[150px] truncate">{level.name}</span>
          </Button>
          {index < path.length - 1 && (
            <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          )}
        </div>
      ))}
    </div>
  )
}
