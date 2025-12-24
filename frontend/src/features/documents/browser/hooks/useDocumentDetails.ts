import { useQuery } from '@tanstack/react-query'
import { api } from '@/core/api/client'

export function useDocumentDetails(documentId: string | null) {
  return useQuery({
    queryKey: ['document-details', documentId],
    queryFn: () => api.getDocumentDetails(documentId!),
    enabled: !!documentId,
  })
}
