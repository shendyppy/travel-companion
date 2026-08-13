import type { LucideIcon } from 'lucide-react'

interface FeatureCardProps {
  icon: LucideIcon
  label: string
  index?: number
}

export function FeatureCard({ icon: Icon, label, index = 0 }: FeatureCardProps) {
  return (
    <div
      className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-secondary/50 border border-border animate-slide-up"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <Icon className="w-4 h-4 text-sky-600 flex-shrink-0" />
      <span className="text-sm text-foreground">{label}</span>
    </div>
  )
}
