import { Bell, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useTimelineEvents } from '@/core/contexts/SSEContext'
import { ConnectionState } from '@/core/hooks/useSSESingleton'

interface HeaderProps {
  title: string
}

export function Header({ title }: HeaderProps) {
  const { connectionState, reconnectAttempts, activeJobs } = useTimelineEvents()

  const getConnectionDisplay = () => {
    switch (connectionState) {
      case ConnectionState.CONNECTED:
        return {
          color: 'bg-green-500',
          text: 'Connected',
          pulse: false,
          showRetry: false,
        }
      case ConnectionState.CONNECTING:
        return {
          color: 'bg-yellow-500',
          text: reconnectAttempts > 0 ? `Reconnecting... (${reconnectAttempts})` : 'Connecting...',
          pulse: true,
          showRetry: reconnectAttempts > 0,
        }
      case ConnectionState.DEGRADED:
        return {
          color: 'bg-orange-500',
          text: 'Degraded',
          pulse: false,
          showRetry: false,
        }
      case ConnectionState.ERROR:
        return {
          color: 'bg-red-500',
          text: `Error (retry ${reconnectAttempts})`,
          pulse: false,
          showRetry: true,
        }
      default:
        return {
          color: 'bg-red-500',
          text: 'Disconnected',
          pulse: false,
          showRetry: false,
        }
    }
  }

  const display = getConnectionDisplay()

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <h1 className="text-xl font-semibold">{title}</h1>

      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search..." className="pl-9" />
        </div>

        {/* Connection status with pulse */}
        <div className="flex items-center gap-2">
          <div
            className={`h-2 w-2 rounded-full ${display.color} ${
              display.pulse ? 'animate-pulse' : ''
            }`}
          />
          <span className="text-sm text-muted-foreground">{display.text}</span>
        </div>

        {/* Active jobs */}
        {activeJobs.length > 0 && (
          <Badge variant="secondary">
            {activeJobs.length} active job{activeJobs.length !== 1 ? 's' : ''}
          </Badge>
        )}

        {/* Notifications */}
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
      </div>
    </header>
  )
}
