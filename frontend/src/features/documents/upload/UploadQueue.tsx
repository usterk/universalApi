import { CheckCircle2, XCircle, Loader2, X, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'

export interface UploadItem {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

interface UploadQueueProps {
  items: UploadItem[]
  onCancel: (id: string) => void
  onRetry: (id: string) => void
  onClearCompleted: () => void
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export function UploadQueue({ items, onCancel, onRetry, onClearCompleted }: UploadQueueProps) {
  if (items.length === 0) {
    return null
  }

  const hasCompleted = items.some(item => item.status === 'success')

  return (
    <div className="border rounded-lg bg-background">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold text-sm">Upload Queue ({items.length})</h3>
        {hasCompleted && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearCompleted}
            className="text-xs"
          >
            Clear Completed
          </Button>
        )}
      </div>

      <ScrollArea className="max-h-[400px]">
        <div className="divide-y">
          {items.map((item) => (
            <div key={item.id} className="p-4 space-y-2">
              {/* File info and status */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {item.status === 'pending' && (
                      <Loader2 className="h-4 w-4 text-muted-foreground animate-spin flex-shrink-0" />
                    )}
                    {item.status === 'uploading' && (
                      <Loader2 className="h-4 w-4 text-primary animate-spin flex-shrink-0" />
                    )}
                    {item.status === 'success' && (
                      <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                    )}
                    {item.status === 'error' && (
                      <XCircle className="h-4 w-4 text-destructive flex-shrink-0" />
                    )}
                    <span className="text-sm font-medium truncate">{item.file.name}</span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatFileSize(item.file.size)}
                    {item.status === 'uploading' && ` • ${item.progress}%`}
                    {item.status === 'error' && item.error && ` • ${item.error}`}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-1 flex-shrink-0">
                  {item.status === 'error' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onRetry(item.id)}
                      className="h-7 w-7 p-0"
                    >
                      <RotateCcw className="h-3 w-3" />
                    </Button>
                  )}
                  {(item.status === 'pending' || item.status === 'uploading' || item.status === 'error') && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onCancel(item.id)}
                      className="h-7 w-7 p-0"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Progress bar */}
              {item.status === 'uploading' && (
                <Progress value={item.progress} className="h-1" />
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
