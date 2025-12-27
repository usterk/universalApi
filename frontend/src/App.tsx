import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/layout/Layout'
import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
import { Timeline } from '@/pages/Timeline'
import { Sources } from '@/pages/Sources'
import { SourceDetail } from '@/pages/SourceDetail'
import { Documents } from '@/pages/Documents'
import { DocumentDetailPage } from '@/pages/DocumentDetailPage'
import { Plugins } from '@/pages/Plugins'
import { UserWorkflows } from '@/pages/UserWorkflows'
import { useAuthStore } from '@/core/stores/auth'
import { api } from '@/core/api/client'
import { SSEProvider } from '@/core/contexts/SSEContext'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, accessToken, setUser } = useAuthStore()
  const location = useLocation()

  // Fetch user data if authenticated but no user loaded
  const { isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const user = await api.me()
      setUser(user)
      return user
    },
    enabled: isAuthenticated && !!accessToken,
    retry: false,
  })

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />

      {/* Protected routes */}
      <Route
        element={
          <ProtectedRoute>
            <SSEProvider>
              <Layout />
            </SSEProvider>
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="timeline" element={<Timeline />} />
        <Route path="sources" element={<Sources />} />
        <Route path="sources/:id" element={<SourceDetail />} />
        <Route path="documents" element={<Documents />} />
        <Route path="documents/:id" element={<DocumentDetailPage />} />
        <Route path="documents/browser" element={<Navigate to="/documents" replace />} />
        <Route path="plugins" element={<Plugins />} />
        <Route path="workflows" element={<UserWorkflows />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
