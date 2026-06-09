import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({ baseURL: BASE_URL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return api(error.config)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

// ─── Auth ───────────────────────────────────────────────────────────────────
export const login = (email: string, password: string) =>
  api.post('/auth/login', { email, password })

export const register = (email: string, password: string, full_name?: string) =>
  api.post('/auth/register', { email, password, full_name })

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
export const getReportDownloadUrl = (reportId: string, format: string) =>
  `/api/v1/reports/${reportId}/download/${format}`
