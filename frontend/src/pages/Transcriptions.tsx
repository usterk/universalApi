import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { FileAudio, Clock, Globe, ChevronRight, Play, Pause } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { apiClient } from '@/core/api/client'

interface Word {
  word: string
  start_time: number
  end_time: number
  confidence: number | null
}

interface TranscriptionDetail {
  id: string
  document_id: string
  full_text: string
  language: string
  language_probability: number | null
  duration_seconds: number | null
  model_used: string
  processing_time_seconds: number | null
  word_count: number
  created_at: string
  words: Word[]
}

interface Transcription {
  id: string
  document_id: string
  full_text: string
  language: string
  language_probability: number | null
  duration_seconds: number | null
  model_used: string
  processing_time_seconds: number | null
  word_count: number
  created_at: string
}

interface TranscriptionListResponse {
  transcriptions: Transcription[]
  total: number
  page: number
  page_size: number
}

function formatDuration(seconds: number) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function TranscriptionDetailDialog({
  transcriptionId,
  open,
  onOpenChange,
}: {
  transcriptionId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [currentTime, setCurrentTime] = useState<number | null>(null)

  const { data: detail, isLoading } = useQuery({
    queryKey: ['transcription', transcriptionId],
    queryFn: async () => {
      const response = await apiClient.get<TranscriptionDetail>(
        `/plugins/audio_transcription/transcriptions/${transcriptionId}`
      )
      return response.data
    },
    enabled: open,
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Transcription Details</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="py-8 text-center text-muted-foreground">Loading...</div>
        ) : detail ? (
          <ScrollArea className="max-h-[60vh]">
            <div className="space-y-6 p-4">
              {/* Metadata */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Language</span>
                  <p className="font-medium flex items-center gap-1">
                    <Globe className="h-4 w-4" />
                    {detail.language}
                    {detail.language_probability && (
                      <span className="text-muted-foreground">
                        ({(detail.language_probability * 100).toFixed(0)}%)
                      </span>
                    )}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Duration</span>
                  <p className="font-medium flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {detail.duration_seconds ? formatDuration(detail.duration_seconds) : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Words</span>
                  <p className="font-medium">{detail.word_count}</p>
                </div>
              </div>

              {/* Full text */}
              <div>
                <h3 className="font-semibold mb-2">Full Text</h3>
                <div className="rounded-lg bg-muted p-4 text-sm leading-relaxed">
                  {detail.full_text}
                </div>
              </div>

              {/* Words with timestamps */}
              <div>
                <h3 className="font-semibold mb-2">Word Timestamps</h3>
                <div className="rounded-lg border p-4">
                  <div className="flex flex-wrap gap-1">
                    {detail.words.map((word, index) => (
                      <button
                        key={index}
                        className={`rounded px-1 py-0.5 text-sm transition-colors hover:bg-primary/20 ${
                          currentTime !== null &&
                          currentTime >= word.start_time &&
                          currentTime <= word.end_time
                            ? 'bg-primary text-primary-foreground'
                            : ''
                        }`}
                        onClick={() => setCurrentTime(word.start_time)}
                        title={`${formatDuration(word.start_time)} - ${formatDuration(word.end_time)}${
                          word.confidence ? ` (${(word.confidence * 100).toFixed(0)}%)` : ''
                        }`}
                      >
                        {word.word}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Model info */}
              <div className="text-sm text-muted-foreground">
                Processed by {detail.model_used} in{' '}
                {detail.processing_time_seconds?.toFixed(2)}s
              </div>
            </div>
          </ScrollArea>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function TranscriptionCard({ transcription }: { transcription: Transcription }) {
  const [detailOpen, setDetailOpen] = useState(false)

  return (
    <>
      <Card
        className="cursor-pointer transition-shadow hover:shadow-md"
        onClick={() => setDetailOpen(true)}
      >
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <FileAudio className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  {transcription.language.toUpperCase()}
                  {transcription.duration_seconds && (
                    <Badge variant="outline">
                      {formatDuration(transcription.duration_seconds)}
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  {transcription.word_count} words - {transcription.model_used}
                </CardDescription>
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-3">
            {transcription.full_text}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            {format(new Date(transcription.created_at), 'PPp')}
          </p>
        </CardContent>
      </Card>

      <TranscriptionDetailDialog
        transcriptionId={transcription.id}
        open={detailOpen}
        onOpenChange={setDetailOpen}
      />
    </>
  )
}

export function Transcriptions() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['transcriptions', page],
    queryFn: async () => {
      const response = await apiClient.get<TranscriptionListResponse>(
        '/plugins/audio_transcription/transcriptions',
        { params: { page, page_size: 20 } }
      )
      return response.data
    },
  })

  return (
    <div className="flex flex-col">
      <Header title="Transcriptions" />

      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">Audio Transcriptions</h2>
          <p className="text-sm text-muted-foreground">
            Browse transcribed audio files with word-level timestamps
          </p>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading...</div>
        ) : data?.transcriptions.length === 0 ? (
          <Card className="py-8">
            <CardContent className="text-center">
              <p className="text-muted-foreground">
                No transcriptions yet. Upload audio files to get started.
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data?.transcriptions.map((t) => (
                <TranscriptionCard key={t.id} transcription={t} />
              ))}
            </div>

            {/* Pagination */}
            {data && data.total > data.page_size && (
              <div className="flex justify-center gap-2">
                <Button
                  variant="outline"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4 text-sm text-muted-foreground">
                  Page {page} of {Math.ceil(data.total / data.page_size)}
                </span>
                <Button
                  variant="outline"
                  disabled={page >= Math.ceil(data.total / data.page_size)}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
