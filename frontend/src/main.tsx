import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/clerk-react'
import './index.css'
import App from './App.tsx'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY')
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ClerkProvider
      publishableKey={PUBLISHABLE_KEY}
      appearance={{
        variables: {
          colorBackground: '#1E1E20',
          colorInputBackground: '#252528',
          colorInputText: '#E4E4E7',
          colorText: '#E4E4E7',
          colorTextSecondary: '#71717A',
          colorPrimary: '#4ADE80',
          colorTextOnPrimaryBackground: '#1A1A1C',
          colorDanger: '#F87171',
          borderRadius: '2px',
          fontFamily: '"Plus Jakarta Sans Variable", system-ui, sans-serif',
        },
        elements: {
          card: { backgroundColor: '#1E1E20', border: '1px solid rgba(255,255,255,0.08)', boxShadow: '0 8px 32px rgba(0,0,0,0.6)' },
          modalBackdrop: { backdropFilter: 'blur(8px)', backgroundColor: 'rgba(0,0,0,0.7)' },
          formFieldInput: { backgroundColor: '#252528', border: '1px solid rgba(255,255,255,0.1)', color: '#E4E4E7' },
          formFieldLabel: { color: '#71717A' },
          dividerLine: { backgroundColor: 'rgba(255,255,255,0.08)' },
          dividerText: { color: '#3F3F46' },
          footerActionLink: { color: '#4ADE80' },
          identityPreviewText: { color: '#E4E4E7' },
          identityPreviewEditButton: { color: '#4ADE80' },
          socialButtonsBlockButton: { backgroundColor: '#2E2E32', border: '1px solid rgba(255,255,255,0.12)', color: '#E4E4E7' },
          socialButtonsBlockButtonText: { color: '#E4E4E7', fontWeight: '500' },
          socialButtonsIconButton: { backgroundColor: '#2E2E32', border: '1px solid rgba(255,255,255,0.12)' },
        },
      }}
    >
      <App />
    </ClerkProvider>
  </StrictMode>,
)
