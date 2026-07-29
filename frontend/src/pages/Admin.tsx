import { useQuery } from '@tanstack/react-query'
import { statsApi } from '../api/client'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function Admin() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => statsApi.get().then(r => r.data),
  })

  if (isLoading) return <div className='flex justify-center py-12'><div className='animate-spin w-8 h-8 border-2 border-vault-amber border-t-transparent rounded-full' /></div>
  if (error) return <div className='text-red-400'>Failed to load stats</div>
  if (!data) return null

  return (
    <div className='space-y-6'>
      <h1 className='text-2xl font-bold'>Admin Dashboard</h1>

      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <div className='card'>
          <div className='text-vault-muted text-sm'>Total Users</div>
          <div className='text-2xl font-mono text-vault-amber mt-1'>{data.total_users}</div>
        </div>
        <div className='card'>
          <div className='text-vault-muted text-sm'>Total Files</div>
          <div className='text-2xl font-mono text-vault-amber mt-1'>{data.total_files}</div>
        </div>
        <div className='card'>
          <div className='text-vault-muted text-sm'>Total Storage</div>
          <div className='text-2xl font-mono text-vault-amber mt-1'>{formatBytes(data.total_bytes)}</div>
        </div>
      </div>

      {data.by_user && data.by_user.length > 0 && (
        <div>
          <h2 className='text-lg font-medium mb-3'>Per-User Breakdown</h2>
          <div className='card !p-0 overflow-hidden'>
            <table className='w-full text-sm'>
              <thead>
                <tr className='border-b border-vault-border text-vault-muted'>
                  <th className='text-left p-3'>User</th>
                  <th className='text-left p-3'>Files</th>
                  <th className='text-left p-3'>Storage</th>
                </tr>
              </thead>
              <tbody>
                {data.by_user.map(u => (
                  <tr key={u.username} className='border-b border-vault-border/50 last:border-0'>
                    <td className='p-3 font-mono'>{u.username}</td>
                    <td className='p-3 font-mono'>{u.count}</td>
                    <td className='p-3 font-mono'>{formatBytes(u.size_bytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
