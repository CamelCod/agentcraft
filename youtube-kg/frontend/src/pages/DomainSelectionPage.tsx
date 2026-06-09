import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { listDomains, approveDomains } from '../api/client'

export default function DomainSelectionPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const { data: domains, isLoading } = useQuery({
    queryKey: ['domains', id],
    queryFn: () => listDomains(id!).then((r) => r.data),
  })

  const approveMutation = useMutation({
    mutationFn: () => approveDomains(id!, Array.from(selected)),
    onSuccess: () => navigate(`/projects/${id}/ingestion`),
  })

  const toggle = (domainId: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(domainId) ? next.delete(domainId) : next.add(domainId)
      return next
    })
  }

  if (isLoading) return <div className="p-6 text-gray-500">Loading detected domains...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Select Knowledge Domains</h1>
      <p className="text-gray-500 text-sm mb-6">
        Select which domains to ingest. Only videos matching selected domains will be processed.
      </p>

      <div className="grid gap-4 mb-8">
        {domains?.map((d: any) => (
          <div
            key={d.id}
            onClick={() => toggle(d.id)}
            className={`bg-white border-2 rounded-xl p-5 cursor-pointer transition-all ${
              selected.has(d.id) ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={selected.has(d.id)}
                    onChange={() => toggle(d.id)}
                    className="w-4 h-4 text-primary-600"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <h3 className="font-semibold text-gray-900">{d.domain_name}</h3>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {d.video_count} videos
                  </span>
                </div>
                {d.description && <p className="text-sm text-gray-500 mt-2 ml-7">{d.description}</p>}
                {d.representative_topics?.length > 0 && (
                  <div className="flex gap-2 flex-wrap mt-2 ml-7">
                    {d.representative_topics.map((t: string) => (
                      <span key={t} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="ml-4 text-right">
                <div className="text-lg font-bold text-gray-900">
                  {Math.round(d.confidence_score * 100)}%
                </div>
                <div className="text-xs text-gray-400">confidence</div>
                <div className="mt-2 w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${d.confidence_score * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => approveMutation.mutate()}
          disabled={selected.size === 0 || approveMutation.isPending}
          className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2.5 rounded-lg font-medium disabled:opacity-50"
        >
          {approveMutation.isPending ? 'Starting ingestion...' : `Approve ${selected.size} domain${selected.size !== 1 ? 's' : ''} & Start Ingestion`}
        </button>
        <button onClick={() => navigate('/projects')} className="px-6 py-2.5 border rounded-lg text-sm">
          Cancel
        </button>
      </div>
    </div>
  )
}
