import { useState } from 'react'
import type { FileItem } from '../types'
import { filesApi } from '../api/client'
import ConfirmDialog from './ConfirmDialog'

interface FileCardProps {
  file: FileItem
  onRename: (id: string, name: string) => void
  onDelete: (id: string) => void
  onRestore?: (id: string) => void
  onPreview?: (file: FileItem) => void
  onDeletePermanent?: (id: string) => void
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function getIcon(mime: string): string {
  if (mime.startsWith('image/')) return '🖼'
  if (mime.startsWith('video/')) return '🎥'
  if (mime.startsWith('audio/')) return '🎵'
  if (mime.includes('pdf')) return '📄'
  if (mime.includes('zip') || mime.includes('rar')) return '📦'
  if (mime.includes('text') || mime.includes('json')) return '📝'
  return '📁'
}

export default function FileCard({ file, onRename, onDelete, onRestore, onPreview, onDeletePermanent }: FileCardProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [showRenamePrompt, setShowRenamePrompt] = useState(false)
  const [renameValue, setRenameValue] = useState('')
  const isPreviewable = file.mime_type.startsWith('image/') || file.mime_type.startsWith('video/') || file.mime_type.startsWith('audio/') || file.mime_type.includes('pdf')

  return (
    <div className='file-card group overflow-hidden'>
      {/* Thumbnail */}
      {file.mime_type.startsWith('image/') && (
        <div className='relative h-36 -mx-4 -mt-4 mb-3 bg-vault-bg overflow-hidden'>
          <img
            src={filesApi.preview(file.id)}
            alt={file.display_name}
            className='w-full h-full object-cover transition-transform duration-300 group-hover:scale-105'
            loading='lazy'
            onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
          <div className='absolute inset-0 bg-gradient-to-t from-vault-surface/80 via-transparent to-transparent' />
        </div>
      )}
      {file.mime_type.startsWith('video/') && (
        <div className='relative h-36 -mx-4 -mt-4 mb-3 bg-vault-bg overflow-hidden flex items-center justify-center'>
          <video
            src={filesApi.preview(file.id)}
            className='w-full h-full object-cover'
            preload='metadata'
            onError={(e) => { (e.target as HTMLVideoElement).style.display = 'none' }}
          />
          <div className='absolute inset-0 flex items-center justify-center'>
            <div className='w-12 h-12 rounded-full bg-black/50 flex items-center justify-center backdrop-blur-sm'>
              <svg className='w-6 h-6 text-white ml-0.5' fill='currentColor' viewBox='0 0 24 24'><path d='M8 5v14l11-7z'/></svg>
            </div>
          </div>
          <div className='absolute inset-0 bg-gradient-to-t from-vault-surface/80 via-transparent to-transparent' />
        </div>
      )}
      <div className='flex items-start justify-between mb-3'>
        <div className='flex items-center gap-3'>
          {!file.mime_type.startsWith('image/') && !file.mime_type.startsWith('video/') && (
            <div className='text-2xl'>{getIcon(file.mime_type)}</div>
          )}
          <div className='min-w-0'>
            <div className='font-medium truncate max-w-[200px]' title={file.display_name}>{file.display_name}</div>
            <div className='text-xs text-vault-muted font-mono mt-0.5'>{formatSize(file.size_bytes)}</div>
          </div>
        </div>
        <div className='flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity'>
          {isPreviewable && onPreview && (
            <button onClick={() => onPreview(file)} className='btn-secondary !px-2 !py-1 text-xs'>
              Preview
            </button>
          )}
          <a href={filesApi.download(file.id)} className='btn-primary !px-2 !py-1 text-xs'>Download</a>
        </div>
      </div>
      <div className='flex items-center justify-between mt-3 pt-2 border-t border-vault-border/50'>
        <span className='uuid-stamp truncate max-w-[180px]' title={file.id}>{file.id.slice(0, 8)}...{file.id.slice(-4)}</span>
        <span className='text-xs text-vault-muted'>{formatDate(file.created_at)}</span>
      </div>
      {showDeleteConfirm && (
        <ConfirmDialog
          open={showDeleteConfirm}
          title={file.is_trashed ? 'Delete forever?' : 'Move to trash?'}
          message={file.is_trashed
            ? `Permanently delete "${file.display_name}"? This removes it from Telegram and cannot be undone.`
            : `Move "${file.display_name}" to trash? You can restore it later.`
          }
          confirmLabel={file.is_trashed ? 'Delete Forever' : 'Move to Trash'}
          danger={file.is_trashed}
          onConfirm={() => {
            setShowDeleteConfirm(false)
            if (file.is_trashed && onDeletePermanent) {
              onDeletePermanent(file.id)
            } else {
              onDelete(file.id)
            }
          }}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}

      {!file.is_trashed ? (
        <div className='flex gap-2 mt-2'>
          <button onClick={() => {
            setRenameValue(file.display_name)
            setShowRenamePrompt(true)
          }} className='text-xs text-vault-muted hover:text-vault-text transition-colors'>Rename</button>
          <button onClick={() => setShowDeleteConfirm(true)} className='text-xs text-red-400 hover:text-red-300 transition-colors'>Delete</button>
        </div>
      ) : (
        <div className='flex gap-2 mt-2'>
          {onRestore && (
            <button onClick={() => onRestore(file.id)} className='text-xs text-vault-amber hover:text-vault-amber/80 transition-colors'>Restore</button>
          )}
          {onDeletePermanent && (
            <button onClick={() => setShowDeleteConfirm(true)} className='text-xs text-red-400 hover:text-red-300 transition-colors'>Delete forever</button>
          )}
        </div>
      )}

      {showRenamePrompt && (
        <div className='fixed inset-0 z-[110] flex items-center justify-center p-4' onClick={() => setShowRenamePrompt(false)}>
          <div className='absolute inset-0 bg-black/60 backdrop-blur-sm' />
          <div onClick={(e) => e.stopPropagation()} className='relative bg-vault-surface border border-vault-border rounded-xl shadow-2xl w-full max-w-sm p-6'>
            <h3 className='text-lg font-semibold mb-2'>Rename file</h3>
            <input
              className='input-field mt-3'
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && renameValue.trim()) {
                  onRename(file.id, renameValue.trim())
                  setShowRenamePrompt(false)
                }
                if (e.key === 'Escape') setShowRenamePrompt(false)
              }}
              autoFocus
            />
            <div className='flex justify-end gap-3 mt-4'>
              <button onClick={() => setShowRenamePrompt(false)} className='btn-secondary !px-4 !py-2 text-sm'>Cancel</button>
              <button onClick={() => { if (renameValue.trim()) { onRename(file.id, renameValue.trim()); setShowRenamePrompt(false) } }} className='btn-primary !px-4 !py-2 text-sm'>Rename</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
