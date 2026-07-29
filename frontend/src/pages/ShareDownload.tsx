import { useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

export default function ShareDownload() {
  const { token } = useParams<{ token: string }>()
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    setError('')
    try {
      const res = await axios.get('/s/' + token, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      const disposition = res.headers['content-disposition']
      const match = disposition?.match(/filename="(.+)"/)
      a.download = match?.[1] || 'download'
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to download')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className='min-h-screen flex items-center justify-center bg-vault-bg px-4'>
      <div className='card max-w-sm w-full text-center space-y-4'>
        <div className='text-5xl opacity-30'>📦</div>
        <h1 className='text-xl font-medium'>Shared File</h1>
        {error && <div className='text-red-400 text-sm bg-red-400/10 rounded-lg p-2'>{error}</div>}
        <button onClick={handleDownload} disabled={downloading} className='btn-primary w-full'>
          {downloading ? 'Downloading...' : 'Download File'}
        </button>
        <p className='text-xs text-vault-muted'>Powered by Trove</p>
      </div>
    </div>
  )
}
