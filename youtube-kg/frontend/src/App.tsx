import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/LoginPage'
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
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <AppShell>
                <Routes>
                  <Route path="/" element={<Navigate to="/projects" replace />} />
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
