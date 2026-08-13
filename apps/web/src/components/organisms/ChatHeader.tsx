import { Plane, MoreVertical } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatHeaderProps {
  isLoading?: boolean
  isVisible?: boolean
}

export function ChatHeader({ isLoading, isVisible = true }: ChatHeaderProps) {
  if (!isVisible) return null

  return (
    <header className="flex-shrink-0 border-b border-border bg-background animate-fade-in">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-sky-100 text-sky-600">
          <Plane className="w-5 h-5" />
        </div>

        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold text-foreground">
            Travel Assistant
          </h1>
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                'w-2 h-2 rounded-full',
                isLoading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-500'
              )}
            />
            <span className="text-xs text-muted-foreground">
              {isLoading ? 'Typing...' : 'Online'}
            </span>
          </div>
        </div>

        <button
          className="p-2 rounded-lg hover:bg-accent transition-colors"
          aria-label="More options"
        >
          <MoreVertical className="w-5 h-5 text-muted-foreground" />
        </button>
      </div>
    </header>
  )
}
