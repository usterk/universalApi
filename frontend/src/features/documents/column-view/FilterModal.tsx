import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Filter } from 'lucide-react'

interface FilterModalProps {
  open: boolean
  onClose: () => void
}

export function FilterModal({ open, onClose }: FilterModalProps) {
  const handleApply = () => {
    // TODO: Apply filters to document query
    onClose()
  }

  const handleClear = () => {
    // TODO: Clear all filters
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            <DialogTitle>Filter Documents</DialogTitle>
          </div>
          <DialogDescription className="sr-only">
            Filter documents by type, source, date range, and sort order
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* TODO: Add filter controls */}
          <div className="text-sm text-muted-foreground text-center p-8">
            Filter controls coming soon...
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleClear}>
            Clear
          </Button>
          <Button onClick={handleApply}>
            Apply
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
