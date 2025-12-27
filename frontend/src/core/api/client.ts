import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/core/stores/auth'

const API_BASE_URL = '/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle 401 and refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token, refresh_token } = response.data
          useAuthStore.getState().setTokens(access_token, refresh_token)

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }
          return apiClient(originalRequest)
        } catch {
          useAuthStore.getState().logout()
        }
      } else {
        useAuthStore.getState().logout()
      }
    }

    return Promise.reject(error)
  }
)

// API types
export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  created_at: string
}

export interface Source {
  id: string
  name: string
  description: string | null
  is_active: boolean
  api_key_prefix: string
  properties: Record<string, unknown>
  created_at: string
}

export interface SourceCreate {
  name: string
  description?: string
  properties?: Record<string, unknown>
}

export interface SourceWithKey extends Source {
  api_key: string
  workflows_imported?: number
}

export interface DocumentType {
  id: string
  name: string
  display_name: string
  description: string | null
  registered_by: string
  mime_types: string[]
  created_at: string
}

export interface Document {
  id: string
  type_name: string
  type_display_name: string
  owner_id: string
  source_id: string | null
  parent_id: string | null
  storage_plugin: string
  filepath: string
  content_type: string
  size_bytes: number
  checksum: string
  properties: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface PluginInfo {
  name: string
  version: string
  display_name: string
  description: string
  is_enabled: boolean
  input_types: string[]
  output_type: string
  priority: number
  dependencies: string[]
  max_concurrent_jobs: number
  color: string
}

export interface ProcessingJob {
  id: string
  document_id: string
  plugin_name: string
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  progress_message: string | null
  result: Record<string, unknown> | null
  error_message: string | null
  output_document_id: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface WorkflowStep {
  id: string
  sequence_number: number
  plugin_name: string
  display_name: string
  input_types: string[]
  output_type: string | null
  color: string
  settings: Record<string, unknown>
  is_enabled: boolean
}

export interface Workflow {
  document_type: string
  steps: WorkflowStep[]
}

export interface AvailablePlugin {
  name: string
  display_name: string
  description: string
  input_types: string[]
  output_type: string | null
  color: string
  compatible_with_step: number | null
}

export interface AddWorkflowStepRequest {
  plugin_name: string
  sequence_number: number
  settings?: Record<string, unknown>
}

export interface ReorderWorkflowRequest {
  steps: Array<{ id: string; sequence_number: number }>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface DocumentTreeNode {
  id: string
  type_name: string
  type_display_name: string
  owner_id: string
  source_id: string | null
  parent_id: string | null
  storage_plugin: string
  filepath: string
  content_type: string
  size_bytes: number
  properties: Record<string, unknown>
  created_at: string
  updated_at: string
  children: DocumentTreeNode[]
}

export interface DocumentTreeResponse {
  items: DocumentTreeNode[]
  total: number
  page: number
  page_size: number
}

export interface ProcessingJobResponse {
  id: string
  plugin_name: string
  status: string
  progress: number
  progress_message: string | null
  result: Record<string, unknown> | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface SystemEventResponse {
  id: string
  event_type: string
  source: string
  severity: string
  payload: Record<string, unknown>
  created_at: string
}

export interface DocumentDetailsResponse {
  document: Document
  parent: Document | null
  children: Document[]
  processing_jobs: ProcessingJobResponse[]
  system_events: SystemEventResponse[]
}

// API functions
export const api = {
  // Auth
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/login', data)
    return response.data
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  me: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  // Sources
  getSources: async (page = 1, pageSize = 20): Promise<PaginatedResponse<Source>> => {
    const response = await apiClient.get('/sources', { params: { page, page_size: pageSize } })
    return response.data
  },

  getSource: async (id: string): Promise<Source> => {
    const response = await apiClient.get(`/sources/${id}`)
    return response.data
  },

  createSource: async (data: SourceCreate): Promise<SourceWithKey> => {
    const response = await apiClient.post('/sources', data)
    return response.data
  },

  deleteSource: async (id: string): Promise<void> => {
    await apiClient.delete(`/sources/${id}`)
  },

  regenerateSourceKey: async (id: string): Promise<{ api_key: string }> => {
    const response = await apiClient.post(`/sources/${id}/regenerate-key`)
    return response.data
  },

  // Workflows
  getWorkflow: async (sourceId: string, documentType: string): Promise<Workflow> => {
    const response = await apiClient.get(`/sources/${sourceId}/workflows/${documentType}`)
    return response.data
  },

  getAvailablePluginsForWorkflow: async (
    sourceId: string,
    documentType: string,
    currentStep?: number
  ): Promise<AvailablePlugin[]> => {
    const params = currentStep ? { current_step: currentStep } : {}
    const response = await apiClient.get(
      `/sources/${sourceId}/workflows/${documentType}/available-plugins`,
      { params }
    )
    return response.data
  },

  addWorkflowStep: async (
    sourceId: string,
    documentType: string,
    data: AddWorkflowStepRequest
  ): Promise<WorkflowStep> => {
    const response = await apiClient.post(
      `/sources/${sourceId}/workflows/${documentType}/steps`,
      data
    )
    return response.data
  },

  deleteWorkflowStep: async (
    sourceId: string,
    documentType: string,
    stepId: string
  ): Promise<void> => {
    await apiClient.delete(`/sources/${sourceId}/workflows/${documentType}/steps/${stepId}`)
  },

  reorderWorkflow: async (
    sourceId: string,
    documentType: string,
    data: ReorderWorkflowRequest
  ): Promise<Workflow> => {
    const response = await apiClient.put(
      `/sources/${sourceId}/workflows/${documentType}/reorder`,
      data
    )
    return response.data
  },

  // User Workflows
  getUserWorkflow: async (documentType: string): Promise<Workflow> => {
    const response = await apiClient.get(`/workflows/${documentType}`)
    return response.data
  },

  getAvailablePluginsForUserWorkflow: async (
    documentType: string,
    currentStep?: number
  ): Promise<AvailablePlugin[]> => {
    const params = currentStep ? { current_step: currentStep } : {}
    const response = await apiClient.get(
      `/workflows/${documentType}/available-plugins`,
      { params }
    )
    return response.data
  },

  addUserWorkflowStep: async (
    documentType: string,
    data: AddWorkflowStepRequest
  ): Promise<WorkflowStep> => {
    const response = await apiClient.post(`/workflows/${documentType}/steps`, data)
    return response.data
  },

  deleteUserWorkflowStep: async (
    documentType: string,
    stepId: string
  ): Promise<void> => {
    await apiClient.delete(`/workflows/${documentType}/steps/${stepId}`)
  },

  reorderUserWorkflow: async (
    documentType: string,
    data: ReorderWorkflowRequest
  ): Promise<Workflow> => {
    const response = await apiClient.put(`/workflows/${documentType}/reorder`, data)
    return response.data
  },

  // Document Types
  getDocumentTypes: async (): Promise<DocumentType[]> => {
    const response = await apiClient.get('/documents/types')
    return response.data
  },

  // Documents
  getDocuments: async (
    page = 1,
    pageSize = 20,
    typeId?: string,
    sourceId?: string
  ): Promise<PaginatedResponse<Document>> => {
    const params: Record<string, unknown> = { page, page_size: pageSize }
    if (typeId) params.type_id = typeId
    if (sourceId) params.source_id = sourceId
    const response = await apiClient.get('/documents', { params })
    return response.data
  },

  getDocument: async (id: string): Promise<Document> => {
    const response = await apiClient.get(`/documents/${id}`)
    return response.data
  },

  getDocumentChildren: async (id: string): Promise<Document[]> => {
    const response = await apiClient.get(`/documents/${id}/children`)
    return response.data
  },

  deleteDocument: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`)
  },

  // Plugins
  getPlugins: async (): Promise<PluginInfo[]> => {
    const response = await apiClient.get('/plugins')
    return response.data
  },

  getPlugin: async (name: string): Promise<PluginInfo> => {
    const response = await apiClient.get(`/plugins/${name}`)
    return response.data
  },

  enablePlugin: async (name: string): Promise<void> => {
    await apiClient.post(`/plugins/${name}/enable`)
  },

  disablePlugin: async (name: string): Promise<void> => {
    await apiClient.post(`/plugins/${name}/disable`)
  },

  // Jobs
  getJobs: async (
    page = 1,
    pageSize = 20,
    status?: string,
    pluginName?: string
  ): Promise<PaginatedResponse<ProcessingJob>> => {
    const params: Record<string, unknown> = { page, page_size: pageSize }
    if (status) params.status = status
    if (pluginName) params.plugin_name = pluginName
    const response = await apiClient.get('/plugins/jobs', { params })
    return response.data
  },

  getJob: async (id: string): Promise<ProcessingJob> => {
    const response = await apiClient.get(`/jobs/${id}`)
    return response.data
  },

  cancelJob: async (id: string, reason?: string): Promise<void> => {
    await apiClient.post(`/jobs/${id}/cancel`, { reason })
  },

  // Upload
  uploadFile: async (
    file: File,
    sourceApiKey?: string,
    onProgress?: (progress: number) => void
  ): Promise<Document> => {
    const formData = new FormData()
    formData.append('file', file)

    const headers: Record<string, string> = {
      'Content-Type': 'multipart/form-data',
    }
    if (sourceApiKey) {
      headers['X-API-Key'] = sourceApiKey
    }

    const response = await apiClient.post('/plugins/upload/files', formData, {
      headers,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  },

  // Get file content URL (for preview/download)
  getFileContentUrl: (documentId: string, inline: boolean = true): string => {
    const token = useAuthStore.getState().accessToken
    return `/api/v1/plugins/upload/files/${documentId}/content?inline=${inline}&token=${token}`
  },

  // Download file
  downloadFile: async (documentId: string, filename?: string): Promise<void> => {
    const response = await apiClient.get(`/plugins/upload/files/${documentId}/content`, {
      params: { inline: false },
      responseType: 'blob',
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename || 'download')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  // Get documents tree
  getDocumentTree: async (
    page = 1,
    pageSize = 20,
    filters?: {
      type_name?: string
      source_id?: string
      created_after?: string
      created_before?: string
      sort_by?: string
      sort_order?: string
    }
  ): Promise<DocumentTreeResponse> => {
    const params: Record<string, unknown> = { page, page_size: pageSize }
    if (filters) {
      Object.assign(params, filters)
    }
    const response = await apiClient.get('/documents/tree', { params })
    return response.data
  },

  // Get document details
  getDocumentDetails: async (id: string): Promise<DocumentDetailsResponse> => {
    const response = await apiClient.get(`/documents/${id}/details`)
    return response.data
  },
}
