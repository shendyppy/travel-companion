import { Sparkles } from 'lucide-react'

interface SuggestionChipsProps {
  suggestions: string[]
  onSelect: (suggestion: string) => void
  disabled?: boolean
}

export function SuggestionChips({
  suggestions,
  onSelect,
  disabled,
}: SuggestionChipsProps) {
  if (suggestions.length === 0) return null

  return (
    <div className="px-4 pt-3 pb-1">
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-foreground bg-secondary/70 hover:bg-secondary border border-border rounded-full whitespace-nowrap transition-colors disabled:opacity-50 disabled:pointer-events-none animate-slide-up"
            onClick={() => onSelect(suggestion)}
            disabled={disabled}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <Sparkles className="w-3 h-3 text-sky-500" />
            <span>{suggestion}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
