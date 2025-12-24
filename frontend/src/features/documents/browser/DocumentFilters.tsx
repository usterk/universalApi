import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Filter, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { api } from '@/core/api/client'
import type { DocumentFilters as Filters } from './hooks/useDocumentFilters'

interface DocumentFiltersProps {
  filters: Filters
  onUpdateFilter: (key: keyof Filters, value: any) => void
  onClearFilters: () => void
}

export function DocumentFilters({
  filters,
  onUpdateFilter,
  onClearFilters,
}: DocumentFiltersProps) {
  const [collapsed, setCollapsed] = useState(false)

  const { data: types } = useQuery({
    queryKey: ['document-types'],
    queryFn: () => api.getDocumentTypes(),
  })

  const { data: sources } = useQuery({
    queryKey: ['sources'],
    queryFn: () => api.getSources(),
  })

  if (collapsed) {
    return (
      <div className="w-12 border-r p-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(false)}
        >
          <Filter className="h-4 w-4" />
        </Button>
      </div>
    )
  }

  return (
    <div className="w-64 border-r p-4 space-y-4 overflow-auto">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <Filter className="h-4 w-4" />
          Filters
        </h3>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(true)}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Document Type */}
      <div className="space-y-2">
        <Label>Document Type</Label>
        <Select
          value={filters.type_name || 'all'}
          onValueChange={(value) =>
            onUpdateFilter('type_name', value === 'all' ? undefined : value)
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {types?.map((type) => (
              <SelectItem key={type.id} value={type.name}>
                {type.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Source */}
      <div className="space-y-2">
        <Label>Source</Label>
        <Select
          value={filters.source_id || 'all'}
          onValueChange={(value) =>
            onUpdateFilter('source_id', value === 'all' ? undefined : value)
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="All sources" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sources</SelectItem>
            {sources?.items?.map((source) => (
              <SelectItem key={source.id} value={source.id}>
                {source.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Date Range */}
      <div className="space-y-2">
        <Label>Created After</Label>
        <Input
          type="datetime-local"
          value={filters.created_after || ''}
          onChange={(e) => onUpdateFilter('created_after', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label>Created Before</Label>
        <Input
          type="datetime-local"
          value={filters.created_before || ''}
          onChange={(e) => onUpdateFilter('created_before', e.target.value)}
        />
      </div>

      {/* Sort */}
      <div className="space-y-2">
        <Label>Sort By</Label>
        <Select
          value={filters.sort_by}
          onValueChange={(value) => onUpdateFilter('sort_by', value)}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created_at">Created Date</SelectItem>
            <SelectItem value="updated_at">Updated Date</SelectItem>
            <SelectItem value="size_bytes">File Size</SelectItem>
            <SelectItem value="type_name">Type</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Order</Label>
        <Select
          value={filters.sort_order}
          onValueChange={(value) => onUpdateFilter('sort_order', value)}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="desc">Newest First</SelectItem>
            <SelectItem value="asc">Oldest First</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Clear Button */}
      <Button variant="outline" className="w-full" onClick={onClearFilters}>
        Clear Filters
      </Button>
    </div>
  )
}
