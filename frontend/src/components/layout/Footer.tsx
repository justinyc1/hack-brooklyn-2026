import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="mt-auto border-t border-ink-700/50 bg-ink-950 py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 md:flex-row">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-ember">◆</span>
          <span className="font-sans text-lg font-semibold text-paper">Intervue</span>
          <span className="font-mono text-xs text-paper-faint ml-3">v0.1.0</span>
        </div>

        <div className="flex items-center gap-8">
          {[
            { to: '/setup', label: 'Practice' },
            { to: '/history', label: 'Sessions' },
          ].map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="font-mono text-xs uppercase tracking-widest text-paper-faint transition-colors duration-200 hover:text-paper-dim"
            >
              {label}
            </Link>
          ))}
        </div>

        <p className="font-mono text-xs text-paper-faint">
          
        </p>
      </div>
    </footer>
  )
}
