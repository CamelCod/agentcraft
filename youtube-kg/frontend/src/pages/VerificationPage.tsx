import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listClaims, listContradictions, triggerVerification } from '../api/client'

type Tab = 'verified' | 'contradicted' | 'insufficient_evidence'

export default function VerificationPage() {
  const { id } = useParams<{ id: string }>()
  const [tab, setTab] = useState<Tab>('verified')
  const qc = useQueryClient()

  const { data: claims } = useQuery({
    queryKey: ['claims', id, tab],
    queryFn: () => listClaims(id!, { verification_status: tab }).then((r) => r.data),
    refetchInterval: 5000,
  })

  const { data: contradictions } = useQuery({
    queryKey: ['contradictions', id],
    queryFn: () => listContradictions(id!).then((r) => r.data),
    enabled: tab === 'contradicted',
  })

  const verifyMutation = useMutation({
    mutationFn: () => triggerVerification(id!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['claims', id] }),
  })

  const tabClass = (t: Tab) =>
    `px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
      tab === t ? 'bg-primary-600 text-white' : 'text-gray-600 hover:bg-gray-100'
    }`

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Verification Dashboard</h1>
        <button
          onClick={() => verifyMutation.mutate()}
          disabled={verifyMutation.isPending}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {verifyMutation.isPending ? 'Running...' : '▶ Run Verification'}
        </button>
      </div>

      <div className="flex gap-2 mb-6">
        {(['verified', 'contradicted', 'insufficient_evidence'] as Tab[]).map((t) => (
          <button key={t} className={tabClass(t)} onClick={() => setTab(t)}>
            {t.replace('_', ' ')}
          </button>
        ))}
      </div>

      {tab === 'contradicted' && contradictions?.length ? (
        <div className="space-y-4">
          {contradictions.map((c: any) => (
            <div key={`${c.claim_a_id}-${c.claim_b_id}`} className="bg-white border border-red-200 rounded-xl p-5">
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="bg-red-50 rounded-lg p-3">
                  <p className="text-xs text-red-500 font-medium mb-1">Claim A</p>
                  <p className="text-sm text-gray-800">{c.claim_a_text}</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3">
                  <p className="text-xs text-red-500 font-medium mb-1">Claim B</p>
                  <p className="text-sm text-gray-800">{c.claim_b_text}</p>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                Similarity: {Math.round((c.similarity || 0) * 100)}% · {c.reasoning}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {claims?.map((c: any) => (
            <div key={c.id} className="bg-white border rounded-xl p-4">
              <p className="text-sm font-medium text-gray-900">{c.text}</p>
              <div className="flex items-center gap-3 mt-2">
                <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${(c.confidence_score || 0) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 w-10 text-right">
                  {Math.round((c.confidence_score || 0) * 100)}%
                </span>
                <span className="text-xs text-gray-400">{c.domain}</span>
                <span className="text-xs text-gray-400">{c.occurrence_count || 1} occurrences</span>
              </div>
            </div>
          ))}
          {!claims?.length && (
            <p className="text-gray-400 text-sm">No claims in this category. Run verification first.</p>
          )}
        </div>
      )}
    </div>
  )
}
