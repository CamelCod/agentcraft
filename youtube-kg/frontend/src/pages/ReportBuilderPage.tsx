import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { listReports, createReport, downloadReport } from '../api/client'

const FORMATS = ['pdf', 'html', 'markdown', 'docx', 'json']

export default function ReportBuilderPage() {
  const { id } = useParams<{ id: string }>()
  const [title, setTitle] = useState('Knowledge Report')
  const [threshold, setThreshold] = useState(0.65)
  const [selectedFormats, setSelectedFormats] = useState(new Set(['pdf', 'html', 'json']))
  const [includeContradictions, setIncludeContradictions] = useState(true)

  const { data: reports, refetch } = useQuery({
    queryKey: ['reports', id],
    queryFn: () => listReports(id).then((r) => r.data),
    refetchInterval: 5000,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      createReport(id!, title, {
        confidence_threshold: threshold,
        formats: Array.from(selectedFormats),
        include_contradictions: includeContradictions,
      }),
    onSuccess: () => refetch(),
  })

  const toggleFormat = (fmt: string) => {
    setSelectedFormats((prev) => {
      const next = new Set(prev)
      next.has(fmt) ? next.delete(fmt) : next.add(fmt)
      return next
    })
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Report Builder</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Builder form */}
        <div className="bg-white border rounded-xl p-6">
          <h2 className="font-semibold mb-4">Generate New Report</h2>

          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-1">Report Title</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Confidence Threshold: {Math.round(threshold * 100)}%
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Export Formats</label>
              <div className="flex gap-2 flex-wrap">
                {FORMATS.map((fmt) => (
                  <button
                    key={fmt}
                    onClick={() => toggleFormat(fmt)}
                    className={`px-3 py-1.5 text-xs rounded-lg border font-medium transition-colors ${
                      selectedFormats.has(fmt)
                        ? 'bg-primary-600 text-white border-primary-600'
                        : 'text-gray-600 border-gray-300 hover:border-primary-400'
                    }`}
                  >
                    {fmt.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeContradictions}
                onChange={(e) => setIncludeContradictions(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">Include contradictions section</span>
            </label>

            <button
              onClick={() => createMutation.mutate()}
              disabled={!title || selectedFormats.size === 0 || createMutation.isPending}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white py-2.5 rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {createMutation.isPending ? 'Queuing report...' : 'Generate Report'}
            </button>
          </div>
        </div>

        {/* Reports list */}
        <div className="bg-white border rounded-xl p-6">
          <h2 className="font-semibold mb-4">Generated Reports</h2>
          {!reports?.length ? (
            <p className="text-gray-400 text-sm">No reports yet</p>
          ) : (
            <div className="space-y-3">
              {reports.map((r: any) => (
                <div key={r.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium text-sm">{r.title}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      r.status === 'ready' ? 'bg-green-100 text-green-700' :
                      r.status === 'generating' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {r.status}
                    </span>
                  </div>
                  {r.status === 'ready' && r.available_formats?.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {r.available_formats.map((fmt: string) => (
                        <button
                          key={fmt}
                          onClick={() => downloadReport(r.id, fmt)}
                          className="text-xs bg-gray-100 hover:bg-primary-100 text-gray-700 px-2 py-1 rounded font-medium transition-colors"
                        >
                          ↓ {fmt.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
