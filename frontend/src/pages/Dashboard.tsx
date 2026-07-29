import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { filesApi, statsApi } from '../api/client'
import SearchBar from '../components/SearchBar'
import FileGrid from '../components/FileGrid'
import UploadZone from '../components/UploadZone'
import PreviewModal from '../components/PreviewModal'
import type { FileItem } from '../types'

interface DashboardProps {
  trashed?: boolean
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function Dashboard({ trashed = false }: DashboardProps) {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('created_at')
  const [typeFilter, setTypeFilter] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [showUpload, setShowUpload] = useState(false)
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null)

  const { data: files = [], isLoading } = useQuery({
    queryKey: ['files', { trashed, search, sort, typeFilter }],
    queryFn: () => filesApi.list({ q: search || undefined, type: typeFilter || undefined, sort, trashed }).then(r => r.data),
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => statsApi.get().then(r => r.data),
    enabled: !trashed,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => filesApi.upload(file, undefined, setProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      setUploading(false)
      setProgress(0)
      setShowUpload(false)
    },
    onError: () => { setUploading(false); setProgress(0) },
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => filesApi.update(id, { display_name: name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['files'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => filesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  const deletePermanentMutation = useMutation({
    mutationFn: (id: string) => filesApi.deletePermanent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  const restoreMutation = useMutation({
    mutationFn: (id: string) => filesApi.restore(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['files'] }),
  })

  const handleUpload = useCallback((file: File) => {
    setUploading(true)
    setProgress(0)
    uploadMutation.mutate(file)
  }, [uploadMutation])

  return (
    <div className='space-y-6'>
      {!trashed && stats && (
        <div className='flex gap-4 text-sm'>
          <div className='card !py-2 !px-4 flex items-center gap-2'>
            <span className='text-vault-muted'>Files:</span>
            <span className='font-mono text-vault-amber'>{stats.total_files}</span>
          </div>
          <div className='card !py-2 !px-4 flex items-center gap-2'>
            <span className='text-vault-muted'>Storage:</span>
            <span className='font-mono text-vault-amber'>{formatBytes(stats.total_bytes)}</span>
          </div>
        </div>
      )}

      <div className='flex items-center gap-3'>
        <SearchBar
          value={search} onChange={setSearch}
          sort={sort} onSortChange={setSort}
          typeFilter={typeFilter} onTypeFilterChange={setTypeFilter}
        />
        <button onClick={() => setShowUpload(!showUpload)} className='btn-primary whitespace-nowrap'>
          {showUpload ? 'Cancel' : '+ Upload'}
        </button>
      </div>

      {showUpload && <UploadZone onUpload={handleUpload} isUploading={uploading} progress={progress} />}

      {previewFile && (
        <PreviewModal file={previewFile} onClose={() => setPreviewFile(null)} />
      )}

      {isLoading ? (
        <div className='flex justify-center py-12'><div className='animate-spin w-8 h-8 border-2 border-vault-amber border-t-transparent rounded-full' /></div>
      ) : (
        <FileGrid
          files={files}
          onRename={(id, name) => renameMutation.mutate({ id, name })}
          onDelete={(id) => deleteMutation.mutate(id)}
          onRestore={trashed ? (id) => restoreMutation.mutate(id) : undefined}
          onPreview={setPreviewFile}
          onDeletePermanent={trashed ? (id) => deletePermanentMutation.mutate(id) : undefined}
        />
      )}
    </div>
  )
}
