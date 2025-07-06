import { Button } from '@/components/ui/button'
import { ThemeToggle } from './theme-toggle'
import { Menu } from 'lucide-react'

export function Header() {
  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
      <Button variant="ghost" size="icon" className="md:hidden">
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle navigation menu</span>
      </Button>
      <div className="flex-1">
        {/* Breadcrumbs or search can go here */}
      </div>
      <ThemeToggle />
    </header>
  )
}