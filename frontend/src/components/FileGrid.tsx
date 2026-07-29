import type { FileItem } from '../types'
import FileCard from './FileCard'

interface FileGridProps {
  files: FileItem[]
  onRename: (id: string, name: string) => void
  onDelete: (id: string) => void
  onRestore?: (id: string) => void
  onPreview?: (file: FileItem) => void
  onDeletePermanent?: (id: string) => void
}

export default function FileGrid({ files, onRename, onDelete, onRestore, onPreview, onDeletePermanent }: FileGridProps) {
  if (files.length === 0) {
    return (
      <div className='text-center py-16'>
        <div className='text-5xl mb-4 opacity-30'>📁</div>
        <h3 className='text-lg font-medium text-vault-muted'>No files yet</h3>
        <p className='text-sm text-vault-muted mt-1'>Drag something in or click to upload</p>
      </div>
    )
  }

  return (
    <div className='grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'>
      {files.map(f => (
        <FileCard key={f.id} file={f} onRename={onRename} onDelete={onDelete} onRestore={onRestore} onPreview={onPreview} onDeletePermanent={onDeletePermanent} />
      ))}
    </div>
  )
}
