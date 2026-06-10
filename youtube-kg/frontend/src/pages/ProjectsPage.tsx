import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { listProjects, createProject, deleteProject } from '../api/client'

const STATUS_COLORS: Record<string, string> = {
  created: 'bg-gray-100 text-gray-700',
  discovering: 'bg-blue-100 text-blue-700',
  domain_pending: 'bg-yellow-100 text-yellow-800',
  ingesting: 'bg-orange-100 text-orange-700',
  extracting: 'bg-purple-100 text-purple-700',
  verifying: 'bg-indigo-100 text-indigo-700',
  ready: 'bg-green-100 text-green-700',
  archived: 'bg-gray-100 text-gray-500',
  error: 'bg-red-100 text-red-700',
}

export default function ProjectsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [creatorUrl, setCreatorUrl] = useState('')
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => listProjects().then((r) => r.data),
    refetchInterval: 5000,
  })

  const createMutation = useMutation({
    mutationFn: () => createProject(name, creatorUrl),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setName('')
      setCreatorUrl('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-sm text-gray-500 mt-1">Manage YouTube creator knowledge extraction projects</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          + New Project
        </button>
      </div>

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-lg font-semibold mb-4">New Project</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Project Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. MKBHD Analysis"
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">YouTube Creator URL</label>
                <input
                  value={creatorUrl}
                  onChange={(e) => setCreatorUrl(e.target.value)}
                  placeholder="https://www.youtube.com/@mkbhd"
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => createMutation.mutate()}
                disabled={!name || !creatorUrl || createMutation.isPending}
                className="flex-1 bg-primary-600 hover:bg-primary-700 text-white py-2 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating...' : 'Create Project'}
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 border rounded-lg text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Projects list */}
      {isLoading ? (
        <p className="text-gray-500">Loading projects...</p>
      ) : !data?.length ? (
        <div className="bg-white border rounded-xl p-12 text-center">
          <p className="text-gray-400 text-lg">No projects yet</p>
          <p className="text-gray-400 text-sm mt-1">Create your first project to get started</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {data.map((p: any) => (
            <div key={p.id} className="bg-white border rounded-xl p-5 flex items-center justify-between hover:border-primary-300 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-gray-900">{p.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[p.status] || 'bg-gray-100'}`}>
                    {p.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-sm text-gray-500 truncate mt-1">{p.creator_url}</p>
                <p className="text-xs text-gray-400 mt-1">{new Date(p.created_at).toLocaleDateString()}</p>
              </div>

              <div className="flex items-center gap-2 ml-4">
                {p.status === 'domain_pending' && (
                  <button
                    onClick={() => navigate(`/projects/${p.id}/domains`)}
                    className="text-xs bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1.5 rounded-lg font-medium"
                  >
                    Select Domains
                  </button>
                )}
                {['ingesting', 'extracting', 'verifying'].includes(p.status) && (
                  <button
                    onClick={() => navigate(`/projects/${p.id}/ingestion`)}
                    className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg"
                  >
                    Monitor
                  </button>
                )}
                {p.status === 'ready' && (
                  <>
                    <button
                      onClick={() => navigate(`/projects/${p.id}/graph`)}
                      className="text-xs bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg"
                    >
                      Explore Graph
                    </button>
                    <button
                      onClick={() => navigate(`/projects/${p.id}/reports`)}
                      className="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg"
                    >
                      Reports
                    </button>
                  </>
                )}
                <button
                  onClick={() => confirm('Delete this project?') && deleteMutation.mutate(p.id)}
                  className="text-xs text-gray-400 hover:text-red-500 px-2 py-1.5"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
