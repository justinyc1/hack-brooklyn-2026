import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useAuth, useClerk } from '@clerk/clerk-react'
import { Toaster } from 'sonner'
import { NavBar } from '@/components/layout/NavBar'
import { Footer } from '@/components/layout/Footer'
import { Home } from '@/routes/Home'
import { Setup } from '@/routes/Setup'
import { TechnicalInterview } from '@/routes/TechnicalInterview'
import { BehavioralInterview } from '@/routes/BehavioralInterview'
import { Feedback } from '@/routes/Feedback'
import { History } from '@/routes/History'
import { NotFound } from '@/routes/NotFound'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isSignedIn, isLoaded } = useAuth()
  const { openSignIn } = useClerk()

  useEffect(() => {
    if (isLoaded && !isSignedIn) openSignIn()
  }, [isLoaded, isSignedIn, openSignIn])

  if (!isLoaded || !isSignedIn) return null
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/setup" element={<ProtectedRoute><Setup /></ProtectedRoute>} />
          <Route path="/interview/:id/technical" element={<ProtectedRoute><TechnicalInterview /></ProtectedRoute>} />
          <Route path="/interview/:id/behavioral" element={<ProtectedRoute><BehavioralInterview /></ProtectedRoute>} />
          <Route path="/feedback/:id" element={<ProtectedRoute><Feedback /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'var(--ink-800)',
            border: '1px solid rgba(250,247,242,0.08)',
            color: 'var(--paper)',
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '12px',
          },
        }}
      />
    </BrowserRouter>
  )
}
