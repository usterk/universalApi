import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TooltipProvider } from '@/components/ui/tooltip'

export function Layout() {
  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto bg-background">
          <Outlet />
        </main>
      </div>
    </TooltipProvider>
  )
}
