import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listVideos, listJobs } from '../api/client'

const STATUS_ICONS: Record<string, string> = {
  discovered: '⏳',
  queued: '📋',
  downloading: '⬇️',
  transcribing: '🎤',
  embedding: '🔢',
  extracting: '🧠',
  completed: '✅',
  skipped: '⏭️',
  error: '❌',
}

export default function IngestionMonitorPage() {
  const { id } = useParams<{ id: string }>()

  const { data: videos } = useQuery({
    queryKey: ['videos', id],
    queryFn: () => listVideos(id!).then((r) => r.data),
    refetchInterval: 3000,
  })

  const { data: jobs } = useQuery({
    queryKey: ['jobs', id],
    queryFn: () => listJobs(id!).then((r) => r.data),
    refetchInterval: 3000,
  })

  const activeJobs = jobs?.filter((j: any) => j.status === 'running') || []
  const completedVideos = videos?.filter((v: any) => v.status === 'completed').length || 0
  const errorVideos = videos?.filter((v: any) => v.status === 'error').length || 0
  const total = videos?.length || 0

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Ingestion Monitor</h1>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Videos', value: total, color: 'text-gray-900' },
          { label: 'Completed', value: completedVideos, color: 'text-green-600' },
          { label: 'Active Jobs', value: activeJobs.length, color: 'text-blue-600' },
          { label: 'Errors', value: errorVideos, color: 'text-red-600' },
        ].map((s) => (
          <div key={s.label} className="bg-white border rounded-xl p-4">
            <p className="text-sm text-gray-500">{s.label}</p>
            <p className={`text-3xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {total > 0 && (
        <div className="bg-white border rounded-xl p-4 mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Overall Progress</span>
            <span>{Math.round((completedVideos / total) * 100)}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all duration-500"
              style={{ width: `${(completedVideos / total) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Video table */}
      <div className="bg-white border rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b bg-gray-50">
          <h2 className="font-semibold text-sm">Videos</h2>
        </div>
        <div className="overflow-auto max-h-96">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-gray-500 text-xs">
                <th className="text-left px-4 py-2">Title</th>
                <th className="text-left px-4 py-2">Status</th>
                <th className="text-left px-4 py-2">Duration</th>
                <th className="text-left px-4 py-2">Error</th>
              </tr>
            </thead>
            <tbody>
              {videos?.map((v: any) => (
                <tr key={v.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 max-w-xs truncate font-medium">{v.title}</td>
                  <td className="px-4 py-2">
                    <span className="flex items-center gap-1.5">
                      {STATUS_ICONS[v.status] || '•'}
                      <span className="text-xs text-gray-600">{v.status}</span>
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-500">
                    {v.duration_seconds ? `${Math.floor(v.duration_seconds / 60)}m` : '—'}
                  </td>
                  <td className="px-4 py-2 text-red-500 text-xs max-w-xs truncate">
                    {v.error_message || ''}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
