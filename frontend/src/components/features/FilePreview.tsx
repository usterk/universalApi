import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Download } from 'lucide-react'
import { api, apiClient, type Document } from '@/core/api/client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import { TranscriptionPreview } from '@/features/documents/preview/TranscriptionPreview'

interface FilePreviewProps {
  document: Document
  maxHeight?: string
  className?: string
  onError?: (error: string) => void
}

export function FilePreview({ document, maxHeight = '70vh', className = '' }: FilePreviewProps) {
  const [error, setError] = useState<string | null>(null)
  const [textContent, setTextContent] = useState<string>('')
  const [isLoadingText, setIsLoadingText] = useState(false)
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [isLoadingBlob, setIsLoadingBlob] = useState(false)

  const contentType = document.content_type
  const filename = (document.properties?.original_filename as string) || 'file'

  // Detect file type from MIME type or filename extension
  const isMarkdown = contentType.includes('markdown') || filename.endsWith('.md')
  const isSourceCode = contentType.startsWith('text/x-') ||
    contentType.includes('javascript') ||
    contentType.includes('typescript') ||
    ['.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php', '.cs', '.swift', '.kt']
      .some(ext => filename.endsWith(ext))

  // Fetch blob for media files (images, audio, video, PDF)
  useEffect(() => {
    const isMediaFile = contentType.startsWith('image/') ||
                        contentType.startsWith('audio/') ||
                        contentType.startsWith('video/') ||
                        contentType === 'application/pdf'

    if (isMediaFile) {
      setIsLoadingBlob(true)
      apiClient.get(`/plugins/upload/files/${document.id}/content`, {
        params: { inline: true },
        responseType: 'blob',
      })
        .then(response => {
          const url = URL.createObjectURL(response.data)
          setBlobUrl(url)
          setIsLoadingBlob(false)
        })
        .catch(() => {
          setError('Failed to load file')
          setIsLoadingBlob(false)
        })

      // Cleanup blob URL on unmount
      return () => {
        if (blobUrl) {
          URL.revokeObjectURL(blobUrl)
        }
      }
    }
  }, [document.id, contentType])

  // Fetch text content for text-based files
  useEffect(() => {
    if (contentType.startsWith('text/') || contentType === 'application/json' || contentType === 'application/xml' || contentType.includes('yaml')) {
      setIsLoadingText(true)
      apiClient.get(`/plugins/upload/files/${document.id}/content`, {
        params: { inline: true },
        responseType: 'text',
      })
        .then(response => {
          setTextContent(response.data)
          setIsLoadingText(false)
        })
        .catch(() => {
          setError('Failed to load file content')
          setIsLoadingText(false)
        })
    }
  }, [document.id, contentType])

  // Detect language for syntax highlighting
  const detectLanguage = (filename: string, mimeType: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase()
    const langMap: Record<string, string> = {
      'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript', 'jsx': 'javascript',
      'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go',
      'rs': 'rust', 'rb': 'ruby', 'php': 'php', 'cs': 'csharp',
      'swift': 'swift', 'kt': 'kotlin', 'md': 'markdown',
      'json': 'json', 'xml': 'xml', 'yaml': 'yaml', 'yml': 'yaml',
      'html': 'html', 'css': 'css', 'scss': 'scss', 'sh': 'bash',
    }
    return langMap[ext || ''] || 'plaintext'
  }

  const handleDownload = async () => {
    try {
      await api.downloadFile(document.id, filename)
    } catch {
      setError('Failed to download file')
    }
  }

  // Check if this is a transcription document (Universal Document Pattern)
  const isTranscription = document.type_name === 'transcription' || document.type_name === 'transcription_words'

  // Render transcription preview for transcription documents
  if (isTranscription) {
    return <TranscriptionPreview document={document} maxHeight={maxHeight} className={className} />
  }

  // Render preview based on content type
  if (error) {
    return (
      <div className={`flex flex-col items-center justify-center gap-4 p-8 ${className}`}>
        <p className="text-destructive">{error}</p>
        <Button onClick={handleDownload}>
          <Download className="mr-2 h-4 w-4" />
          Download File
        </Button>
      </div>
    )
  }

  // Loading state for media files
  if (isLoadingBlob) {
    return <div className={`p-8 text-center ${className}`}>Loading preview...</div>
  }

  // Images
  if (contentType.startsWith('image/') && blobUrl) {
    return (
      <div className={`flex items-center justify-center bg-muted/10 rounded-lg p-4 ${className}`}>
        <img
          src={blobUrl}
          alt={filename}
          style={{ maxHeight }}
          className="max-w-full object-contain"
          onError={() => setError('Failed to load image')}
        />
      </div>
    )
  }

  // Audio
  if (contentType.startsWith('audio/') && blobUrl) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <audio controls className="w-full max-w-xl">
          <source src={blobUrl} type={contentType} />
          Your browser does not support audio playback.
        </audio>
      </div>
    )
  }

  // Video
  if (contentType.startsWith('video/') && blobUrl) {
    return (
      <div className={`flex items-center justify-center bg-black rounded-lg ${className}`}>
        <video controls style={{ maxHeight }} className="w-full">
          <source src={blobUrl} type={contentType} />
          Your browser does not support video playback.
        </video>
      </div>
    )
  }

  // PDF
  if (contentType === 'application/pdf' && blobUrl) {
    return (
      <div className={`w-full bg-muted/10 rounded-lg ${className}`} style={{ height: maxHeight }}>
        <iframe src={blobUrl} className="w-full h-full rounded-lg" title="PDF Preview" />
      </div>
    )
  }

  // Markdown (with rendering)
  if (isMarkdown && textContent) {
    return (
      <ScrollArea className={`rounded-lg border p-4 ${className}`} style={{ maxHeight }}>
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
            {textContent}
          </ReactMarkdown>
        </div>
      </ScrollArea>
    )
  }

  // Source code (with syntax highlighting)
  if (isSourceCode && textContent) {
    const language = detectLanguage(filename, contentType)
    const highlighted = hljs.highlight(textContent, { language, ignoreIllegals: true })

    return (
      <ScrollArea className={`rounded-lg border ${className}`} style={{ maxHeight }}>
        <pre className="p-4 bg-muted/50 m-0">
          <code
            className={`hljs language-${language}`}
            dangerouslySetInnerHTML={{ __html: highlighted.value }}
          />
        </pre>
      </ScrollArea>
    )
  }

  // Plain text or JSON
  if ((contentType.startsWith('text/') || contentType === 'application/json') && textContent) {
    let displayContent = textContent

    // Pretty print JSON
    if (contentType === 'application/json') {
      try {
        displayContent = JSON.stringify(JSON.parse(textContent), null, 2)
      } catch {
        // If JSON parsing fails, just display as-is
      }
    }

    return (
      <ScrollArea className={`rounded-lg border ${className}`} style={{ maxHeight }}>
        <pre className="p-4 bg-muted/50 m-0">
          <code className="text-sm">{displayContent}</code>
        </pre>
      </ScrollArea>
    )
  }

  // XML/YAML (with syntax highlighting)
  if ((contentType.includes('xml') || contentType.includes('yaml')) && textContent) {
    const language = contentType.includes('xml') ? 'xml' : 'yaml'
    const highlighted = hljs.highlight(textContent, { language, ignoreIllegals: true })

    return (
      <ScrollArea className={`rounded-lg border ${className}`} style={{ maxHeight }}>
        <pre className="p-4 bg-muted/50 m-0">
          <code
            className={`hljs language-${language}`}
            dangerouslySetInnerHTML={{ __html: highlighted.value }}
          />
        </pre>
      </ScrollArea>
    )
  }

  // Loading state
  if (isLoadingText) {
    return <div className={`p-8 text-center ${className}`}>Loading preview...</div>
  }

  // Unsupported file type
  return (
    <div className={`flex flex-col items-center justify-center gap-4 p-8 ${className}`}>
      <p className="text-muted-foreground">Preview not available for this file type</p>
      <Button onClick={handleDownload}>
        <Download className="mr-2 h-4 w-4" />
        Download File
      </Button>
    </div>
  )
}
