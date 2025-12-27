import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { WorkflowBuilder } from './WorkflowBuilder'

interface SourceWorkflowsTabProps {
  sourceId: string
}

// Common document types that support workflows
const DOCUMENT_TYPES = [
  { value: 'audio', label: 'Audio' },
  { value: 'video', label: 'Video' },
  { value: 'image', label: 'Image' },
  { value: 'document', label: 'Document' },
  { value: 'text', label: 'Text' },
]

export function SourceWorkflowsTab({ sourceId }: SourceWorkflowsTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold">Processing Workflows</h2>
        <p className="text-muted-foreground">
          Configure how different file types should be processed
        </p>
      </div>

      <Tabs defaultValue="audio" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          {DOCUMENT_TYPES.map((type) => (
            <TabsTrigger key={type.value} value={type.value}>
              {type.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {DOCUMENT_TYPES.map((type) => (
          <TabsContent key={type.value} value={type.value} className="mt-6">
            <WorkflowBuilder
              config={{ type: 'source', sourceId }}
              documentType={type.value}
            />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
