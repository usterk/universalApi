import { useState, useCallback } from 'react'

export interface NavigationLevel {
  documentId: string | null
  name: string
}

export function useColumnNavigation() {
  const [path, setPath] = useState<NavigationLevel[]>([
    { documentId: null, name: 'Home' }
  ])

  const navigateTo = useCallback((documentId: string, name: string) => {
    setPath(prev => [...prev, { documentId, name }])
  }, [])

  const navigateBack = useCallback((level: number) => {
    setPath(prev => prev.slice(0, level + 1))
  }, [])

  const reset = useCallback(() => {
    setPath([{ documentId: null, name: 'Home' }])
  }, [])

  const currentLevel = path.length - 1
  const currentDocumentId = path[path.length - 1]?.documentId || null

  return {
    path,
    currentLevel,
    currentDocumentId,
    navigateTo,
    navigateBack,
    reset,
  }
}
