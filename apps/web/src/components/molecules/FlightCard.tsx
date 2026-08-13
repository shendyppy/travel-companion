import type { FlightInfo } from '@/types'
import { Plane, Clock, Circle } from 'lucide-react'
import { Card } from '@/components/ui'

interface FlightCardProps {
  flight: FlightInfo
}

export function FlightCard({ flight }: FlightCardProps) {
  const formatPrice = (price: number, currency: string) => {
    if (currency === 'IDR') {
      return `Rp ${price.toLocaleString('id-ID')}`
    }
    return `${currency} ${price.toLocaleString()}`
  }

  const formatTime = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleTimeString('id-ID', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateString
    }
  }

  return (
    <Card className="p-3 bg-background">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-sky-100 flex items-center justify-center">
            <Plane className="w-3.5 h-3.5 text-sky-600" />
          </div>
          <span className="text-sm font-medium text-foreground">
            {flight.airline}
          </span>
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          {flight.airline_code}
        </span>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="text-center">
          <p className="text-lg font-semibold text-foreground">
            {formatTime(flight.departure_time)}
          </p>
          <p className="text-xs text-muted-foreground font-medium">
            {flight.origin}
          </p>
        </div>

        <div className="flex-1 flex flex-col items-center gap-1 px-2">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>{flight.duration}</span>
          </div>
          <div className="w-full flex items-center gap-1">
            <Circle className="w-1.5 h-1.5 fill-muted-foreground text-muted-foreground" />
            <div className="flex-1 h-px bg-border relative">
              <Plane className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 text-sky-500" />
            </div>
            <Circle className="w-1.5 h-1.5 fill-muted-foreground text-muted-foreground" />
          </div>
          <span className="text-[10px] text-muted-foreground">
            {flight.stops === 0
              ? 'Direct'
              : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
          </span>
        </div>

        <div className="text-center">
          <p className="text-lg font-semibold text-foreground">
            {formatTime(flight.arrival_time)}
          </p>
          <p className="text-xs text-muted-foreground font-medium">
            {flight.destination}
          </p>
        </div>
      </div>

      <div className="mt-3 pt-2 border-t border-border">
        <p className="text-base font-semibold text-sky-600">
          {formatPrice(flight.price, flight.currency)}
        </p>
      </div>
    </Card>
  )
}
