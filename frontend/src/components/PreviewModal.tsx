import { useEffect, useCallback } from 'react'
import type { FileItem } from '../types'
import { filesApi } from '../api/client'

interface PreviewModalProps {
  file: FileItem | null
  onClose: () => void
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export default function PreviewModal({ file, onClose }: PreviewModalProps) {
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    if (file) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
      return () => {
        document.removeEventListener('keydown', handleKeyDown)
        document.body.style.overflow = ''
      }
    }
  }, [file, handleKeyDown])

  if (!file) return null

  const previewUrl = filesApi.preview(file.id)
  const isImage = file.mime_type.startsWith('image/')
  const isVideo = file.mime_type.startsWith('video/')
  const isAudio = file.mime_type.startsWith('audio/')
  const isPdf = file.mime_type.includes('pdf')

  return (
    <div
      className='fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-8'
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className='absolute inset-0 bg-black/80 backdrop-blur-sm' />

      {/* Modal */}
      <div
        onClick={(e) => e.stopPropagation()}
        className='relative bg-vault-surface border border-vault-border rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col'
      >
        {/* Header */}
        <div className='flex items-center justify-between px-5 py-3 border-b border-vault-border shrink-0'>
          <div className='min-w-0 flex-1'>
            <h2 className='font-medium truncate'>{file.display_name}</h2>
            <p className='text-xs text-vault-muted font-mono'>{formatSize(file.size_bytes)}</p>
          </div>
          <div className='flex items-center gap-2 shrink-0 ml-4'>
            <a
              href={filesApi.download(file.id)}
              className='btn-primary !px-3 !py-1.5 text-xs'
              onClick={onClose}
            >
              Download
            </a>
            <button
              onClick={onClose}
              className='w-8 h-8 flex items-center justify-center rounded-lg hover:bg-vault-border transition-colors text-vault-muted hover:text-vault-text'
            >
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M6 18L18 6M6 6l12 12' />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className='flex-1 overflow-auto p-2 flex items-center justify-center bg-vault-bg/50 rounded-b-2xl min-h-[300px]'>
          {isImage && (
            <img
              src={previewUrl}
              alt={file.display_name}
              className='max-w-full max-h-[70vh] object-contain rounded-lg'
            />
          )}
          {isVideo && (
            <video
              src={previewUrl}
              controls
              autoPlay
              className='max-w-full max-h-[70vh] rounded-lg'
            >
              Your browser does not support video playback.
            </video>
          )}
          {isAudio && (
            <div className='flex flex-col items-center gap-4 p-8'>
              <div className='text-6xl'>🎵</div>
              <audio src={previewUrl} controls autoPlay className='w-full max-w-md' />
            </div>
          )}
          {isPdf && (
            <iframe
              src={previewUrl}
              className='w-full h-[70vh] rounded-lg'
              title={file.display_name}
            />
          )}
          {!isImage && !isVideo && !isAudio && !isPdf && (
            <div className='text-center py-12'>
              <div className='text-5xl mb-4 opacity-30'>📄</div>
              <p className='text-vault-muted'>Preview not available for this file type</p>
              <a
                href={filesApi.download(file.id)}
                className='btn-primary inline-block mt-4'
                onClick={onClose}
              >
                Download instead
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
