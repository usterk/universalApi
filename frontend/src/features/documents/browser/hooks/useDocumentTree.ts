import { useQuery } from '@tanstack/react-query'
import { api } from '@/core/api/client'
import type { DocumentFilters } from './useDocumentFilters'

export function useDocumentTree(page: number, pageSize: number, filters: DocumentFilters) {
  return useQuery({
    queryKey: ['documents-tree', page, pageSize, filters],
    queryFn: () => api.getDocumentTree(page, pageSize, filters),
    keepPreviousData: true,
  })
}
