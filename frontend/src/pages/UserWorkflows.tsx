import { Header } from '@/components/layout/Header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { WorkflowBuilder } from '@/features/sources/components/WorkflowBuilder'

const DOCUMENT_TYPES = [
  { value: 'audio', label: 'Audio' },
  { value: 'video', label: 'Video' },
  { value: 'image', label: 'Image' },
  { value: 'document', label: 'Document' },
  { value: 'text', label: 'Text' },
]

export function UserWorkflows() {
  return (
    <div className="flex flex-col">
      <Header title="Default Workflows" />

      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold">Default Processing Workflows</h2>
          <p className="text-muted-foreground">
            Configure default workflows for files you upload. These settings will be
            automatically applied to new sources you create.
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
                config={{ type: 'user' }}
                documentType={type.value}
              />
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  )
}
