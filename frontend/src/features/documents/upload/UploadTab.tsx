import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { UploadQueue, type UploadItem } from './UploadQueue'
import { api } from '@/core/api/client'
import { cn } from '@/lib/utils'

export function UploadTab() {
  const navigate = useNavigate()
  const [uploadItems, setUploadItems] = useState<UploadItem[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return

    const newItems: UploadItem[] = Array.from(files).map((file) => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      status: 'pending' as const,
      progress: 0,
    }))

    setUploadItems((prev) => [...prev, ...newItems])

    // Start uploading each file
    newItems.forEach((item) => uploadFile(item))
  }, [])

  const uploadFile = async (item: UploadItem) => {
    try {
      // Update status to uploading
      setUploadItems((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: 'uploading' } : i))
      )

      // Upload file with progress tracking
      const response = await api.uploadFile(item.file, undefined, (progress) => {
        setUploadItems((prev) =>
          prev.map((i) => (i.id === item.id ? { ...i, progress } : i))
        )
      })

      // Mark as success
      setUploadItems((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, status: 'success', progress: 100 } : i))
      )

      // Invalidate document queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['documents'] })

      // Redirect to document detail page
      navigate(`/documents/${response.id}`)
    } catch (error) {
      // Mark as error
      setUploadItems((prev) =>
        prev.map((i) =>
          i.id === item.id
            ? {
                ...i,
                status: 'error',
                error: error instanceof Error ? error.message : 'Upload failed',
              }
            : i
        )
      )
    }
  }

  const handleCancel = (id: string) => {
    setUploadItems((prev) => prev.filter((item) => item.id !== id))
  }

  const handleRetry = (id: string) => {
    const item = uploadItems.find((i) => i.id === id)
    if (item) {
      uploadFile({ ...item, status: 'pending', progress: 0, error: undefined })
    }
  }

  const handleClearCompleted = () => {
    setUploadItems((prev) => prev.filter((item) => item.status !== 'success'))
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      handleFileSelect(e.dataTransfer.files)
    },
    [handleFileSelect]
  )

  const handleButtonClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files)
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="h-full flex flex-col gap-4 p-6">
      {/* Drag & Drop Zone */}
      <div
        className={cn(
          'border-2 border-dashed rounded-lg flex-1 min-h-[300px] flex flex-col items-center justify-center gap-4 transition-colors',
          isDragging
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="h-12 w-12 text-muted-foreground" />
        <div className="text-center space-y-2">
          <p className="text-lg font-medium">
            {isDragging ? 'Drop files here' : 'Drag & drop files here'}
          </p>
          <p className="text-sm text-muted-foreground">or</p>
          <Button onClick={handleButtonClick} size="lg">
            Select Files
          </Button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileInputChange}
        />
      </div>

      {/* Upload Queue */}
      {uploadItems.length > 0 && (
        <UploadQueue
          items={uploadItems}
          onCancel={handleCancel}
          onRetry={handleRetry}
          onClearCompleted={handleClearCompleted}
        />
      )}
    </div>
  )
}
