import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Copy, RefreshCw, Trash2, MoreHorizontal } from 'lucide-react'
import { Header } from '@/components/layout/Header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { api, type Source, type SourceWithKey } from '@/core/api/client'

function CreateSourceDialog() {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [createdSource, setCreatedSource] = useState<SourceWithKey | null>(null)
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: api.createSource,
    onSuccess: (data) => {
      setCreatedSource(data)
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  const handleCreate = () => {
    createMutation.mutate({ name, description: description || undefined })
  }

  const handleClose = () => {
    setOpen(false)
    setName('')
    setDescription('')
    setCreatedSource(null)
    createMutation.reset()
  }

  const copyApiKey = () => {
    if (createdSource?.api_key) {
      navigator.clipboard.writeText(createdSource.api_key)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => (v ? setOpen(true) : handleClose())}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Source
        </Button>
      </DialogTrigger>
      <DialogContent>
        {!createdSource ? (
          <>
            <DialogHeader>
              <DialogTitle>Create New Source</DialogTitle>
              <DialogDescription>
                Create a new data source to receive uploads via API
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="My Device"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Input
                  id="description"
                  placeholder="Device description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!name || createMutation.isPending}>
                Create
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Source Created</DialogTitle>
              <DialogDescription>
                Save this API key - you won't be able to see it again!
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>API Key</Label>
                <div className="flex gap-2">
                  <Input value={createdSource.api_key} readOnly className="font-mono text-sm" />
                  <Button variant="outline" size="icon" onClick={copyApiKey}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  Use this key in the X-API-Key header when uploading files
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

function SourceCard({ source }: { source: Source }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showKey, setShowKey] = useState(false)
  const [newKey, setNewKey] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteSource(source.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
  })

  const regenerateMutation = useMutation({
    mutationFn: () => api.regenerateSourceKey(source.id),
    onSuccess: (data) => {
      setNewKey(data.api_key)
      setShowKey(true)
    },
  })

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent"
      onClick={() => navigate(`/sources/${source.id}`)}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2">
            {source.name}
            <Badge variant={source.is_active ? 'default' : 'secondary'}>
              {source.is_active ? 'Active' : 'Inactive'}
            </Badge>
          </CardTitle>
          <CardDescription>{source.description || 'No description'}</CardDescription>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation()
                regenerateMutation.mutate()
              }}
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate API Key
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              onClick={(e) => {
                e.stopPropagation()
                deleteMutation.mutate()
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">API Key Prefix</span>
            <code className="rounded bg-muted px-2 py-0.5">{source.api_key_prefix}...</code>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{new Date(source.created_at).toLocaleDateString()}</span>
          </div>
        </div>

        {showKey && newKey && (
          <div className="mt-4 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-3">
            <p className="text-sm font-medium text-yellow-600 mb-2">
              New API Key (save it now!)
            </p>
            <div className="flex gap-2">
              <Input value={newKey} readOnly className="font-mono text-xs" />
              <Button
                variant="outline"
                size="icon"
                onClick={() => navigator.clipboard.writeText(newKey)}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function Sources() {
  const { data, isLoading } = useQuery({
    queryKey: ['sources'],
    queryFn: () => api.getSources(),
  })

  return (
    <div className="flex flex-col">
      <Header title="Sources" />

      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Data Sources</h2>
            <p className="text-sm text-muted-foreground">
              Manage external data sources and their API keys
            </p>
          </div>
          <CreateSourceDialog />
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-muted-foreground">Loading...</div>
        ) : !data?.items?.length ? (
          <Card className="py-8">
            <CardContent className="text-center">
              <p className="text-muted-foreground mb-4">No sources yet</p>
              <CreateSourceDialog />
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
