import { useState } from 'react'
import { Filter } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ColumnView } from '@/features/documents/column-view/ColumnView'
import { FilterModal } from '@/features/documents/column-view/FilterModal'
import { UploadTab } from '@/features/documents/upload/UploadTab'

// Export formatFileSize for use in other components
export function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export function Documents() {
  const [activeTab, setActiveTab] = useState('browser')
  const [filterModalOpen, setFilterModalOpen] = useState(false)

  return (
    <div className="flex flex-col h-screen">
      <Header title="Documents" />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          {/* Tab bar with filter button */}
          <div className="border-b px-6 pt-6 pb-0">
            <div className="flex items-center justify-between mb-4">
              <TabsList>
                <TabsTrigger value="browser">File Browser</TabsTrigger>
                <TabsTrigger value="upload">Upload File</TabsTrigger>
              </TabsList>

              {/* Filter button (only shown on File Browser tab) */}
              {activeTab === 'browser' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilterModalOpen(true)}
                  className="gap-2"
                >
                  <Filter className="h-4 w-4" />
                  Filter
                </Button>
              )}
            </div>
          </div>

          {/* Tab content */}
          <TabsContent value="browser" className="flex-1 m-0 overflow-hidden">
            <ColumnView />
          </TabsContent>

          <TabsContent value="upload" className="flex-1 m-0 overflow-auto">
            <UploadTab />
          </TabsContent>
        </Tabs>
      </div>

      {/* Filter Modal */}
      <FilterModal open={filterModalOpen} onClose={() => setFilterModalOpen(false)} />
    </div>
  )
}
