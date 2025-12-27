import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Clock, Globe, FileText, AudioLines } from 'lucide-react'
import type { Document } from '@/core/api/client'

interface Word {
  word: string
  start: number
  end: number
  confidence?: number
}

interface TranscriptionPreviewProps {
  document: Document
  maxHeight?: string
  className?: string
}

/**
 * Renders a preview for transcription documents.
 * Shows the full text, metadata, and optionally word-level timestamps.
 */
export function TranscriptionPreview({
  document,
  maxHeight = '70vh',
  className = '',
}: TranscriptionPreviewProps) {
  const properties = document.properties

  const fullText = properties?.full_text as string | undefined
  const language = properties?.language as string | undefined
  const durationSeconds = properties?.duration_seconds as number | undefined
  const modelUsed = properties?.model_used as string | undefined
  const wordCount = properties?.word_count as number | undefined
  const words = properties?.words as Word[] | undefined
  const hasWords = words && words.length > 0

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  const formatLanguage = (lang: string): string => {
    const langNames: Record<string, string> = {
      en: 'English',
      pl: 'Polish',
      de: 'German',
      fr: 'French',
      es: 'Spanish',
      it: 'Italian',
      pt: 'Portuguese',
      ru: 'Russian',
      ja: 'Japanese',
      zh: 'Chinese',
      ko: 'Korean',
      unknown: 'Unknown',
    }
    return langNames[lang] || lang
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Metadata badges */}
      <div className="flex flex-wrap gap-2">
        {language && (
          <Badge variant="outline" className="gap-1">
            <Globe className="h-3 w-3" />
            {formatLanguage(language)}
          </Badge>
        )}
        {durationSeconds && (
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            {formatDuration(durationSeconds)}
          </Badge>
        )}
        {wordCount !== undefined && (
          <Badge variant="outline" className="gap-1">
            <FileText className="h-3 w-3" />
            {wordCount} words
          </Badge>
        )}
        {modelUsed && (
          <Badge variant="secondary" className="gap-1">
            <AudioLines className="h-3 w-3" />
            {modelUsed}
          </Badge>
        )}
      </div>

      {/* Full text */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Transcription</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea style={{ maxHeight }} className="pr-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {fullText || 'No transcription text available.'}
            </p>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Word timestamps (if available) */}
      {hasWords && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Word Timestamps ({words.length} words)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea style={{ maxHeight: '300px' }} className="pr-4">
              <div className="flex flex-wrap gap-1">
                {words.map((word, index) => (
                  <span
                    key={index}
                    className="inline-flex cursor-help items-baseline rounded bg-muted px-1.5 py-0.5 text-sm"
                    title={`${word.start.toFixed(2)}s - ${word.end.toFixed(2)}s${word.confidence !== undefined ? ` (${(word.confidence * 100).toFixed(0)}% confidence)` : ''}`}
                  >
                    {word.word}
                  </span>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
