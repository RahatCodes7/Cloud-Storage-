interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({
  open, title, message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  onConfirm, onCancel
}: ConfirmDialogProps) {
  if (!open) return null

  return (
    <div
      className='fixed inset-0 z-[110] flex items-center justify-center p-4'
      onClick={onCancel}
    >
      <div className='absolute inset-0 bg-black/60 backdrop-blur-sm' />
      <div
        onClick={(e) => e.stopPropagation()}
        className='relative bg-vault-surface border border-vault-border rounded-xl shadow-2xl w-full max-w-sm p-6'
      >
        <h3 className='text-lg font-semibold mb-2'>{title}</h3>
        <p className='text-sm text-vault-muted mb-6'>{message}</p>
        <div className='flex justify-end gap-3'>
          <button onClick={onCancel} className='btn-secondary !px-4 !py-2 text-sm'>
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={danger
              ? 'bg-red-500 text-white font-medium px-4 py-2 rounded-lg hover:bg-red-600 transition-colors text-sm'
              : 'btn-primary !px-4 !py-2 text-sm'
            }
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
