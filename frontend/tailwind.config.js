/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#1A1A1C',
          900: '#1E1E20',
          800: '#252528',
          700: '#2E2E32',
          600: '#3F3F46',
        },
        paper: {
          DEFAULT: '#E4E4E7',
          dim: '#71717A',
          faint: '#3F3F46',
        },
        ember: {
          DEFAULT: '#4ADE80',
          soft: '#86EFAC',
          muted: 'rgba(74,222,128,0.1)',
        },
        moss: {
          DEFAULT: '#4ADE80',
          muted: 'rgba(74,222,128,0.1)',
        },
        crimson: {
          DEFAULT: '#F87171',
          muted: 'rgba(248,113,113,0.12)',
        },
      },
      fontFamily: {
        display: ['"Fraunces Variable"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans Variable"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 0 rgba(255,255,255,0.03), 0 4px 16px -4px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.05)',
        'card-hover': '0 1px 0 rgba(255,255,255,0.05), 0 8px 24px -8px rgba(0,0,0,0.6), inset 0 0 0 1px rgba(74,222,128,0.15)',
        ember: '0 0 32px -4px rgba(74,222,128,0.35)',
        'ember-sm': '0 0 12px -2px rgba(74,222,128,0.2)',
        subtle: 'inset 0 0 0 1px rgba(255,255,255,0.05)',
      },
      keyframes: {
        'pulse-ember': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.5', transform: 'scale(0.85)' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'transcript-in': {
          from: { opacity: '0', transform: 'translateX(-8px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        'pulse-ember': 'pulse-ember 1.6s ease-in-out infinite',
        'fade-up': 'fade-up 0.5s ease-out both',
        'transcript-in': 'transcript-in 0.3s ease-out both',
      },
    },
  },
  plugins: [],
}
