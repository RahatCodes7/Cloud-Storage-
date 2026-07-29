import { useState, useRef, useCallback } from 'react'

interface UploadZoneProps {
  onUpload: (file: File) => void
  isUploading: boolean
  progress: number
}

export default function UploadZone({ onUpload, isUploading, progress }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onUpload(file)
  }, [onUpload])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onUpload(file)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ' + (dragging ? 'border-vault-amber bg-vault-amber/5' : 'border-vault-border hover:border-vault-amber/50')}
    >
      <input ref={inputRef} type='file' className='hidden' onChange={handleChange} />
      {isUploading ? (
        <div className='space-y-2'>
          <div className='text-vault-amber'>Uploading...</div>
          <div className='w-full bg-vault-bg rounded-full h-2'>
            <div className='bg-vault-amber h-2 rounded-full transition-all duration-300' style={{ width: progress + '%' }} />
          </div>
          <div className='text-sm text-vault-muted font-mono'>{progress}%</div>
        </div>
      ) : (
        <div className='space-y-2'>
          <div className='text-3xl'>↑</div>
          <div className='text-vault-muted'>{dragging ? 'Drop it here' : 'Drag & drop or click to upload'}</div>
          <div className='text-xs text-vault-muted'>Any file, any size</div>
        </div>
      )}
    </div>
  )
}
