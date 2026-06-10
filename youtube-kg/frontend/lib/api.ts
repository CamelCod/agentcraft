const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://home.agentcraftconsultancy.com'

export async function apiCall(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  data?: unknown,
  token?: string
) {
  const url = `${API_BASE}${endpoint}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, {
    method,
    headers,
    body: data ? JSON.stringify(data) : undefined,
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export async function registerUser(email: string, password: string, token?: string) {
  return apiCall('/api/v1/auth/register', 'POST', { email, password }, token)
}

export async function getProjects(token: string) {
  return apiCall('/api/v1/projects', 'GET', undefined, token)
}

export async function createProject(data: { name: string; creator_url: string }, token: string) {
  return apiCall('/api/v1/projects', 'POST', data, token)
}

export async function getProject(projectId: string, token: string) {
  return apiCall(`/api/v1/projects/${projectId}`, 'GET', undefined, token)
}
