import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core'
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Plus, GripVertical, Trash2, ArrowRight } from 'lucide-react'
import { api, type WorkflowStep, type AvailablePlugin } from '@/core/api/client'

interface WorkflowBuilderConfig {
  type: 'source' | 'user'
  sourceId?: string  // Required if type='source'
}

interface WorkflowBuilderProps {
  config: WorkflowBuilderConfig
  documentType: string
}

export function WorkflowBuilder({ config, documentType }: WorkflowBuilderProps) {
  const queryClient = useQueryClient()
  const [isAddingStep, setIsAddingStep] = useState(false)

  // Generate query key based on config type
  const getQueryKey = () => {
    if (config.type === 'source') {
      return ['workflows', config.sourceId, documentType]
    } else {
      return ['workflows', 'user', documentType]
    }
  }

  // Fetch current workflow
  const { data: workflow, isLoading } = useQuery({
    queryKey: getQueryKey(),
    queryFn: () => {
      if (config.type === 'source') {
        return api.getWorkflow(config.sourceId!, documentType)
      } else {
        return api.getUserWorkflow(documentType)
      }
    },
  })

  // Fetch available plugins (only when adding)
  const { data: availablePlugins } = useQuery({
    queryKey: [...getQueryKey(), 'available-plugins'],
    queryFn: () => {
      const lastStep = workflow?.steps?.[workflow.steps.length - 1]
      const currentStep = lastStep ? lastStep.sequence_number + 1 : 1
      if (config.type === 'source') {
        return api.getAvailablePluginsForWorkflow(config.sourceId!, documentType, currentStep)
      } else {
        return api.getAvailablePluginsForUserWorkflow(documentType, currentStep)
      }
    },
    enabled: isAddingStep && !!workflow,
  })

  const addStepMutation = useMutation({
    mutationFn: (pluginName: string) => {
      const nextSequence = (workflow?.steps?.length || 0) + 1
      if (config.type === 'source') {
        return api.addWorkflowStep(config.sourceId!, documentType, {
          plugin_name: pluginName,
          sequence_number: nextSequence,
        })
      } else {
        return api.addUserWorkflowStep(documentType, {
          plugin_name: pluginName,
          sequence_number: nextSequence,
        })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getQueryKey() })
      setIsAddingStep(false)
    },
  })

  const deleteStepMutation = useMutation({
    mutationFn: (stepId: string) => {
      if (config.type === 'source') {
        return api.deleteWorkflowStep(config.sourceId!, documentType, stepId)
      } else {
        return api.deleteUserWorkflowStep(documentType, stepId)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getQueryKey() })
    },
  })

  const reorderMutation = useMutation({
    mutationFn: (steps: Array<{ id: string; sequence_number: number }>) => {
      if (config.type === 'source') {
        return api.reorderWorkflow(config.sourceId!, documentType, { steps })
      } else {
        return api.reorderUserWorkflow(documentType, { steps })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getQueryKey() })
    },
  })

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id || !workflow?.steps) return

    const oldIndex = workflow.steps.findIndex((s) => s.id === active.id)
    const newIndex = workflow.steps.findIndex((s) => s.id === over.id)

    // Reorder steps array
    const reordered = arrayMove(workflow.steps, oldIndex, newIndex)

    // Update sequence numbers
    const updatedSteps = reordered.map((step, index) => ({
      id: step.id,
      sequence_number: index + 1,
    }))

    reorderMutation.mutate(updatedSteps)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <p className="text-muted-foreground">Loading workflow...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold capitalize">
          Workflow for {documentType} files
        </h3>
        <p className="text-sm text-muted-foreground">
          Define the processing pipeline for {documentType} documents from this source
        </p>
      </div>

      {/* Workflow Steps */}
      {workflow?.steps && workflow.steps.length > 0 ? (
        <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext
            items={workflow.steps.map((s) => s.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-3">
              {workflow.steps.map((step, index) => (
                <WorkflowStepCard
                  key={step.id}
                  step={step}
                  stepNumber={index + 1}
                  onDelete={() => deleteStepMutation.mutate(step.id)}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      ) : (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            <p>No workflow configured for {documentType} files.</p>
            <p className="text-sm">Add plugins below to start processing.</p>
          </CardContent>
        </Card>
      )}

      {/* Add Step Button / Selector */}
      {!isAddingStep ? (
        <Button
          onClick={() => setIsAddingStep(true)}
          variant="outline"
          className="w-full"
          disabled={addStepMutation.isPending}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Plugin to Workflow
        </Button>
      ) : (
        <div className="space-y-2">
          <p className="text-sm font-medium">Select a plugin to add:</p>
          <div className="grid gap-2">
            {availablePlugins?.map((plugin) => (
              <Card
                key={plugin.name}
                className="cursor-pointer transition-colors hover:bg-accent"
                onClick={() => addStepMutation.mutate(plugin.name)}
              >
                <CardContent className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium">{plugin.display_name}</h4>
                      <p className="text-xs text-muted-foreground">{plugin.description}</p>
                      <div className="mt-2 flex gap-2">
                        <Badge variant="secondary" className="text-xs">
                          Accepts: {plugin.input_types.join(', ')}
                        </Badge>
                        {plugin.output_type && (
                          <Badge variant="outline" className="text-xs">
                            <ArrowRight className="mr-1 h-3 w-3" />
                            {plugin.output_type}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {availablePlugins?.length === 0 && (
              <Alert>
                <AlertDescription>
                  No compatible plugins available. Check output type compatibility.
                </AlertDescription>
              </Alert>
            )}
          </div>
          <Button variant="ghost" onClick={() => setIsAddingStep(false)}>
            Cancel
          </Button>
        </div>
      )}
    </div>
  )
}

// Sortable Workflow Step Card
interface WorkflowStepCardProps {
  step: WorkflowStep
  stepNumber: number
  onDelete: () => void
}

function WorkflowStepCard({ step, stepNumber, onDelete }: WorkflowStepCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: step.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <Card ref={setNodeRef} style={style}>
      <CardContent className="flex items-center gap-3 p-4">
        {/* Drag handle */}
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing"
        >
          <GripVertical className="h-5 w-5 text-muted-foreground" />
        </div>

        {/* Step number */}
        <div
          className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full font-semibold text-primary-foreground"
          style={{ backgroundColor: step.color }}
        >
          {stepNumber}
        </div>

        {/* Plugin info */}
        <div className="flex-1">
          <h4 className="font-medium">{step.display_name}</h4>
          <div className="mt-1 flex gap-2">
            <Badge variant="secondary" className="text-xs">
              {step.input_types.join(', ')}
            </Badge>
            {step.output_type && (
              <>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <Badge variant="outline" className="text-xs">
                  {step.output_type}
                </Badge>
              </>
            )}
          </div>
        </div>

        {/* Delete button */}
        <Button variant="ghost" size="icon" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardContent>
    </Card>
  )
}
