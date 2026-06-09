import { useQuery } from '@tanstack/react-query'
import { getMe } from '../api/client'
import { useAuthStore } from '../store/authStore'

export default function AdminPage() {
  const { data: me } = useQuery({
    queryKey: ['me'],
    queryFn: () => getMe().then((r) => r.data),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Administration</h1>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white border rounded-xl p-6">
          <h2 className="font-semibold mb-4">Current User</h2>
          {me && (
            <dl className="space-y-2 text-sm">
              <div className="flex gap-2">
                <dt className="text-gray-500 w-24">Email</dt>
                <dd className="font-medium">{me.email}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="text-gray-500 w-24">Role</dt>
                <dd>
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full font-medium">
                    {me.role}
                  </span>
                </dd>
              </div>
              <div className="flex gap-2">
                <dt className="text-gray-500 w-24">Status</dt>
                <dd className="text-green-600 font-medium">{me.is_active ? 'Active' : 'Inactive'}</dd>
              </div>
            </dl>
          )}
        </div>

        <div className="bg-white border rounded-xl p-6">
          <h2 className="font-semibold mb-4">External Dashboards</h2>
          <div className="space-y-2">
            {[
              { label: 'Celery Worker Monitor (Flower)', path: '/flower' },
              { label: 'Neo4j Browser', path: 'http://localhost:7474' },
              { label: 'MinIO Console', path: '/minio' },
              { label: 'Grafana', path: '/grafana' },
              { label: 'API Documentation', path: '/api/docs' },
            ].map((l) => (
              <a
                key={l.label}
                href={l.path}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors text-sm"
              >
                <span className="font-medium">{l.label}</span>
                <span className="text-gray-400">↗</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
