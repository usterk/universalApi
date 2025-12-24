import { useState } from 'react'
import { Breadcrumb } from './Breadcrumb'
import { Column } from './Column'
import { PreviewPanel } from './PreviewPanel'
import { useColumnNavigation } from './hooks/useColumnNavigation'
import { useDocumentChildren } from './hooks/useDocumentChildren'
import type { Document } from '@/core/api/client'

interface DocumentColumnProps {
  parentId: string | null
  selectedId: string | null
  onSelect: (document: Document) => void
  onNavigate: (document: Document) => void
}

function DocumentColumn({ parentId, selectedId, onSelect, onNavigate }: DocumentColumnProps) {
  const { data: documents = [], isLoading } = useDocumentChildren(parentId)

  return (
    <Column
      documents={documents}
      selectedId={selectedId}
      onSelect={onSelect}
      onNavigate={onNavigate}
      isLoading={isLoading}
    />
  )
}

export function ColumnView() {
  const { path, navigateTo, navigateBack } = useColumnNavigation()
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  const handleSelect = (document: Document) => {
    setSelectedDocument(document)
    setIsPreviewOpen(true)
  }

  const handleNavigate = (document: Document) => {
    const filename = (document.properties?.original_filename as string) || document.filepath
    navigateTo(document.id, filename)
    setSelectedDocument(null)
    setIsPreviewOpen(false)
  }

  const handleBreadcrumbClick = (level: number) => {
    navigateBack(level)
    setSelectedDocument(null)
    setIsPreviewOpen(false)
  }

  const handleClosePreview = () => {
    setIsPreviewOpen(false)
  }

  // Build array of column parent IDs
  // First column shows root documents (parentId = null from path[0])
  // Each subsequent column shows children of the document at that path level
  const columnParentIds = path.map(level => level.documentId)

  // Add one more column to show children of the last navigated document
  const lastLevel = path[path.length - 1]
  if (lastLevel?.documentId) {
    columnParentIds.push(lastLevel.documentId)
  }

  return (
    <div className="h-full flex flex-col">
      {/* Breadcrumb navigation */}
      <Breadcrumb path={path} onNavigateBack={handleBreadcrumbClick} />

      {/* Columns container */}
      <div className="flex-1 flex overflow-x-auto overflow-y-hidden">
        {columnParentIds.map((parentId, index) => (
          <DocumentColumn
            key={`${parentId}-${index}`}
            parentId={parentId}
            selectedId={selectedDocument?.id || null}
            onSelect={handleSelect}
            onNavigate={handleNavigate}
          />
        ))}
      </div>

      {/* Preview panel (slides in from right) */}
      <PreviewPanel
        document={selectedDocument}
        isOpen={isPreviewOpen}
        onClose={handleClosePreview}
      />
    </div>
  )
}
