import { Plane, Building2, MapPin, Wallet } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface WelcomeScreenProps {
  greeting?: string
}

interface Feature {
  icon: LucideIcon
  label: string
}

const features: Feature[] = [
  { icon: Plane, label: 'Flight Search' },
  { icon: Building2, label: 'Hotels' },
  { icon: MapPin, label: 'Destinations' },
  { icon: Wallet, label: 'Budget Tips' },
]

export function WelcomeScreen({ greeting }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 animate-fade-in">
      <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-sky-100 text-sky-600 mb-6">
        <Plane className="w-8 h-8" />
      </div>

      <h2 className="text-xl font-semibold text-foreground text-center mb-2">
        {greeting || 'Hi, where would you like to go?'}
      </h2>

      <p className="text-sm text-muted-foreground text-center max-w-sm mb-8">
        I can help you find flights, hotels, and plan your perfect trip.
      </p>

      <div className="grid grid-cols-2 gap-3 w-full max-w-xs">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <div
              key={index}
              className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-secondary/50 border border-border animate-slide-up"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <Icon className="w-4 h-4 text-sky-600 flex-shrink-0" />
              <span className="text-sm text-foreground">{feature.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
