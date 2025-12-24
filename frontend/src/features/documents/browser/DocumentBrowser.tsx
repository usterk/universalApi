import { useState } from 'react'
import { Header } from '@/components/layout/Header'
import { DocumentTreeView } from './DocumentTreeView'
import { DocumentFilters } from './DocumentFilters'
import { DocumentDetails } from './DocumentDetails'
import { useDocumentFilters } from './hooks/useDocumentFilters'

export function DocumentBrowser() {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const { filters, updateFilter, clearFilters } = useDocumentFilters()
  const [page, setPage] = useState(1)

  const handleSelectDocument = (id: string) => {
    setSelectedDocumentId(id)
    setDetailsOpen(true)
  }

  return (
    <div className="flex flex-col h-screen">
      <Header title="Document Browser" />

      <div className="flex flex-1 overflow-hidden">
        {/* Filter Sidebar */}
        <DocumentFilters
          filters={filters}
          onUpdateFilter={updateFilter}
          onClearFilters={clearFilters}
        />

        {/* Main View */}
        <div className="flex-1 overflow-auto p-6">
          <DocumentTreeView
            page={page}
            pageSize={20}
            filters={filters}
            onSelectDocument={handleSelectDocument}
            onPageChange={setPage}
          />
        </div>
      </div>

      {/* Details Slide-in Panel */}
      <DocumentDetails
        documentId={selectedDocumentId}
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
      />
    </div>
  )
}
