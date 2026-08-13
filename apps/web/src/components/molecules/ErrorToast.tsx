import { AlertCircle, X } from 'lucide-react'

interface ErrorToastProps {
  message: string
  onDismiss: () => void
}

export function ErrorToast({ message, onDismiss }: ErrorToastProps) {
  return (
    <div
      className="flex items-center gap-3 px-4 py-3 bg-destructive/10 border border-destructive/20 rounded-xl animate-slide-up cursor-pointer"
      onClick={onDismiss}
    >
      <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
      <span className="flex-1 text-sm text-destructive">{message}</span>
      <X className="w-4 h-4 text-destructive/70" />
    </div>
  )
}
