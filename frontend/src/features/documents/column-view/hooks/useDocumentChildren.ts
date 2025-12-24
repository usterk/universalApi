import { useQuery } from '@tanstack/react-query'
import { api, type Document } from '@/core/api/client'

/**
 * Hook to fetch children documents for a given parent.
 *
 * @param parentId - Parent document ID, or null for root documents
 * @returns TanStack Query result with documents array
 */
export function useDocumentChildren(parentId: string | null) {
  return useQuery({
    queryKey: ['documents', 'children', parentId],
    queryFn: async () => {
      if (parentId === null) {
        // Fetch root documents (documents with no parent)
        const response = await api.getDocumentTree(1, 100)
        // Return only top-level items, ignore nested children
        return response.items.map(item => ({
          id: item.id,
          type_name: item.type_name,
          type_display_name: item.type_display_name,
          owner_id: item.owner_id,
          source_id: item.source_id,
          parent_id: item.parent_id,
          storage_plugin: item.storage_plugin,
          filepath: item.filepath,
          content_type: item.content_type,
          size_bytes: item.size_bytes,
          checksum: '', // Not included in tree response
          properties: item.properties,
          created_at: item.created_at,
          updated_at: item.updated_at,
        })) as Document[]
      } else {
        // Fetch children of specific document
        return await api.getDocumentChildren(parentId)
      }
    },
    staleTime: 30 * 1000, // Cache for 30 seconds
  })
}
