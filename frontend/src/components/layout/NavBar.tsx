import { Link, useLocation, useNavigate } from 'react-router-dom'
import { SignedIn, SignedOut, UserButton, SignInButton } from '@clerk/clerk-react'
import { cn } from '@/lib/cn'

function AccountIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="5.5" r="2.5" />
      <path d="M2.5 13.5c0-2.485 2.462-4.5 5.5-4.5s5.5 2.015 5.5 4.5" />
    </svg>
  )
}

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
            { to: '/problems', label: 'Problems' },
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
                variables: {
                  colorText: '#FAF7F2',
                  colorTextSecondary: '#A8A29E',
                  colorBackground: '#0F0F12',
                  colorInputBackground: '#1A1A1F',
                },
                elements: {
                  avatarBox: 'w-8 h-8',
                  userButtonPopoverCard: 'bg-ink-900 border border-ink-700/60 shadow-card !text-paper',
                  userButtonPopoverActionButton: '!text-paper hover:!bg-ink-800',
                  userButtonPopoverActionButtonText: '!text-paper',
                  userButtonPopoverActionButtonIcon: '!text-paper-faint',
                  userButtonPopoverCustomItemButton: '!text-paper hover:!bg-ink-800',
                  userButtonPopoverCustomItemButtonText: '!text-paper',
                  userButtonPopoverCustomItemButtonIconBox: '!text-paper-faint',
                  userPreviewMainIdentifier: '!text-paper !font-medium',
                  userPreviewSecondaryIdentifier: '!text-paper-faint',
                  userButtonPopoverFooter: '!hidden',
                  badge: '!hidden',
                },
              }}
            >
              <UserButton.MenuItems>
                <UserButton.Action
                  label="Account"
                  labelIcon={<AccountIcon />}
                  onClick={() => navigate('/account')}
                />
              </UserButton.MenuItems>
            </UserButton>
          </SignedIn>
        </div>
      </nav>
    </header>
  )
}
