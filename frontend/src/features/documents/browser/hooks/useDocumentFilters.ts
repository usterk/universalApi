import { useState } from 'react'

export interface DocumentFilters {
  type_name?: string
  source_id?: string
  created_after?: string
  created_before?: string
  sort_by: string
  sort_order: 'asc' | 'desc'
}

export function useDocumentFilters() {
  const [filters, setFilters] = useState<DocumentFilters>({
    sort_by: 'created_at',
    sort_order: 'desc',
  })

  const updateFilter = (key: keyof DocumentFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const clearFilters = () => {
    setFilters({
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  }

  return {
    filters,
    updateFilter,
    clearFilters,
  }
}
