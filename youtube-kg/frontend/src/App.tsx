import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { supabase } from './lib/supabase'
import { useAuthStore } from './store/authStore'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import ProjectsPage from './pages/ProjectsPage'
import DomainSelectionPage from './pages/DomainSelectionPage'
import IngestionMonitorPage from './pages/IngestionMonitorPage'
import GraphExplorerPage from './pages/GraphExplorerPage'
import VerificationPage from './pages/VerificationPage'
import ReportBuilderPage from './pages/ReportBuilderPage'
import AdminPage from './pages/AdminPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  const { setSession } = useAuthStore()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session))
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })
    return () => subscription.unsubscribe()
  }, [setSession])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <AppShell>
                <Routes>
                  <Route path="/" element={<Navigate to="/projects" replace />} />
                  <Route path="/dashboard" element={<Navigate to="/projects" replace />} />
                  <Route path="/projects" element={<ProjectsPage />} />
                  <Route path="/projects/:id/domains" element={<DomainSelectionPage />} />
                  <Route path="/projects/:id/ingestion" element={<IngestionMonitorPage />} />
                  <Route path="/projects/:id/graph" element={<GraphExplorerPage />} />
                  <Route path="/projects/:id/verification" element={<VerificationPage />} />
                  <Route path="/projects/:id/reports" element={<ReportBuilderPage />} />
                  <Route path="/admin" element={<AdminPage />} />
                </Routes>
              </AppShell>
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
