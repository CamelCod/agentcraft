import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listClaims, getClaim, getGraphOverview } from '../api/client'

export default function GraphExplorerPage() {
  const { id } = useParams<{ id: string }>()
  const [selectedClaim, setSelectedClaim] = useState<any>(null)
  const [filter, setFilter] = useState('')

  const { data: overview } = useQuery({
    queryKey: ['graph-overview', id],
    queryFn: () => getGraphOverview(id!).then((r) => r.data),
  })

  const { data: claims } = useQuery({
    queryKey: ['claims', id],
    queryFn: () => listClaims(id!).then((r) => r.data),
  })

  const filtered = claims?.filter((c: any) =>
    !filter || c.text?.toLowerCase().includes(filter.toLowerCase())
  )

  const STATUS_BADGE: Record<string, string> = {
    verified: 'bg-green-100 text-green-800',
    contradicted: 'bg-red-100 text-red-800',
    insufficient_evidence: 'bg-gray-100 text-gray-600',
    pending: 'bg-yellow-100 text-yellow-800',
  }

  return (
    <div className="flex h-full gap-4">
      {/* Left: Claims list */}
      <div className="w-96 flex flex-col gap-4">
        <div>
          <h1 className="text-xl font-bold mb-1">Graph Explorer</h1>
          {overview && (
            <p className="text-xs text-gray-500">
              {Object.entries(overview).map(([k, v]) => `${v} ${k}`).join(' · ')}
            </p>
          )}
        </div>

        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter claims..."
          className="border rounded-lg px-3 py-2 text-sm w-full"
        />

        <div className="overflow-auto space-y-2 flex-1">
          {filtered?.map((c: any) => (
            <div
              key={c.id}
              onClick={() => setSelectedClaim(c)}
              className={`bg-white border rounded-lg p-3 cursor-pointer hover:border-primary-300 transition-colors ${
                selectedClaim?.id === c.id ? 'border-primary-500 bg-primary-50' : ''
              }`}
            >
              <p className="text-sm font-medium text-gray-900 line-clamp-2">{c.text}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[c.verification_status] || 'bg-gray-100'}`}>
                  {c.verification_status}
                </span>
                <span className="text-xs text-gray-400">{c.domain}</span>
                <span className="text-xs text-gray-400 ml-auto">
                  {Math.round((c.confidence_score || 0) * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Claim detail */}
      <div className="flex-1 bg-white border rounded-xl p-6 overflow-auto">
        {!selectedClaim ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Select a claim to view details and evidence</p>
          </div>
        ) : (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">{selectedClaim.text}</h2>
            <div className="flex gap-3 mb-6">
              <span className={`text-sm px-3 py-1 rounded-full ${STATUS_BADGE[selectedClaim.verification_status]}`}>
                {selectedClaim.verification_status}
              </span>
              <span className="text-sm text-gray-500">Confidence: {Math.round((selectedClaim.confidence_score || 0) * 100)}%</span>
              <span className="text-sm text-gray-500">Domain: {selectedClaim.domain}</span>
            </div>

            <h3 className="font-semibold text-gray-700 mb-3">Evidence</h3>
            {selectedClaim.evidence?.length ? (
              <div className="space-y-3">
                {selectedClaim.evidence.map((ev: any, i: number) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-4 border">
                    <blockquote className="text-sm text-gray-700 italic border-l-4 border-primary-300 pl-3 mb-2">
                      "{ev.excerpt}"
                    </blockquote>
                    {ev.youtube_id && (
                      <a
                        href={`https://www.youtube.com/watch?v=${ev.youtube_id}&t=${Math.floor(ev.start_time || 0)}s`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-primary-600 hover:underline"
                      >
                        ▶ {ev.youtube_id} @ {Math.floor(ev.start_time || 0)}s – {Math.floor(ev.end_time || 0)}s
                      </a>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No evidence chunks loaded yet.</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
