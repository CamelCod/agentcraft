import axios from 'axios'
import { supabase } from '../lib/supabase'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({ baseURL: BASE_URL })

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const { data: { session } } = await supabase.auth.refreshSession()
      if (session) {
        error.config.headers.Authorization = `Bearer ${session.access_token}`
        return api(error.config)
      }
      await supabase.auth.signOut()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ─── Auth ───────────────────────────────────────────────────────────────────
export const getMe = () => api.get('/auth/me')

// ─── Projects ────────────────────────────────────────────────────────────────
export const listProjects = () => api.get('/projects')
export const createProject = (name: string, creator_url: string) =>
  api.post('/projects', { name, creator_url })
export const getProject = (id: string) => api.get(`/projects/${id}`)
export const deleteProject = (id: string) => api.delete(`/projects/${id}`)

// ─── Domains ─────────────────────────────────────────────────────────────────
export const listDomains = (projectId: string) =>
  api.get(`/projects/${projectId}/domains`)
export const approveDomains = (projectId: string, domainIds: string[]) =>
  api.post(`/projects/${projectId}/domains/approve`, { domain_ids: domainIds })

// ─── Videos / Jobs ───────────────────────────────────────────────────────────
export const listVideos = (projectId: string, status?: string) =>
  api.get(`/projects/${projectId}/videos`, { params: status ? { status } : {} })
export const listJobs = (projectId: string) =>
  api.get(`/projects/${projectId}/jobs`)

// ─── Graph ───────────────────────────────────────────────────────────────────
export const getGraphOverview = (projectId: string) =>
  api.get(`/projects/${projectId}/graph/overview`)
export const listClaims = (projectId: string, params?: Record<string, string | number>) =>
  api.get(`/projects/${projectId}/graph/claims`, { params })
export const getClaim = (projectId: string, claimId: string) =>
  api.get(`/projects/${projectId}/graph/claims/${claimId}`)
export const listContradictions = (projectId: string) =>
  api.get(`/projects/${projectId}/graph/contradictions`)

// ─── Verification ────────────────────────────────────────────────────────────
export const triggerVerification = (projectId: string) =>
  api.post(`/projects/${projectId}/verify`)

// ─── Reports ─────────────────────────────────────────────────────────────────
export const listReports = (projectId?: string) =>
  api.get('/reports', { params: projectId ? { project_id: projectId } : {} })
export const createReport = (projectId: string, title: string, config: object) =>
  api.post('/reports', { project_id: projectId, title, config })
export const downloadReport = async (reportId: string, format: string): Promise<void> => {
  const { data } = await api.get(`/reports/${reportId}/download/${format}`)
  window.open(data.url, '_blank', 'noopener,noreferrer')
}
