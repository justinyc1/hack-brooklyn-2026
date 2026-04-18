import { Link, useLocation, useNavigate } from 'react-router-dom'
import { SignedIn, SignedOut, UserButton, SignInButton } from '@clerk/clerk-react'
import { cn } from '@/lib/cn'

export function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()
  const isInterviewRoom = location.pathname.includes('/interview/')

  if (isInterviewRoom) return null

  return (
    <header className="sticky top-0 z-50 border-b border-ink-700/60 bg-ink-950/90 backdrop-blur-md">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="font-mono text-xs text-ember">◆</span>
          <span className="font-sans text-xl font-bold tracking-tight text-paper group-hover:text-ember transition-colors duration-200">
            Intervue
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {[
            { to: '/history', label: 'Sessions' },
            { to: '/setup', label: 'Practice' },
          ].map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                'font-mono text-xs uppercase tracking-widest transition-colors duration-200',
                location.pathname === to
                  ? 'text-paper'
                  : 'text-paper-dim hover:text-paper'
              )}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <SignedOut>
            <SignInButton mode="modal">
              <button className="group relative overflow-hidden rounded-sm border border-ember/30 bg-ember/8 px-4 py-2 font-mono text-xs uppercase tracking-widest text-ember transition-all duration-200 hover:border-ember/60 hover:bg-ember/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ember">
                Sign in
                <span className="ml-2 opacity-60 group-hover:opacity-100 transition-opacity">→</span>
              </button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <button
              onClick={() => navigate('/setup')}
              className="group relative overflow-hidden rounded-sm border border-ember/30 bg-ember/8 px-4 py-2 font-mono text-xs uppercase tracking-widest text-ember transition-all duration-200 hover:border-ember/60 hover:bg-ember/15 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ember"
            >
              Begin session
              <span className="ml-2 opacity-60 group-hover:opacity-100 transition-opacity">→</span>
            </button>
            <UserButton
              appearance={{
                elements: {
                  avatarBox: 'w-8 h-8',
                  userButtonPopoverCard: 'bg-ink-900 border border-ink-700/60 shadow-card',
                },
              }}
            />
          </SignedIn>
        </div>
      </nav>
    </header>
  )
}
