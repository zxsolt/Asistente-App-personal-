/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"IBM Plex Serif"', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      },
      colors: {
        canvas: '#0c0c0f',
        surface: {
          DEFAULT: '#13131a',
          2: '#1a1a24',
          3: '#22222f',
        },
        border: {
          DEFAULT: '#272737',
          2: '#363650',
        },
        ink: {
          DEFAULT: '#ddd8cf',
          muted: '#7c7c8a',
          dim: '#484858',
        },
        amber: {
          DEFAULT: '#d4a43a',
          dim: 'rgba(212,164,58,0.1)',
          bright: '#e8b84b',
        },
        work: '#5b9cf6',
        study: '#a78bfa',
        status: {
          pending: '#6b7280',
          progress: '#3b82f6',
          done: '#22c55e',
          discarded: '#ef4444',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-down': 'slideDown 0.25s ease-out',
        'complete-pop': 'completePop 0.4s cubic-bezier(0.34,1.56,0.64,1)',
        'particle-fly': 'particleFly 0.8s ease-out forwards',
        'win-card-in': 'winCardIn 0.5s cubic-bezier(0.34,1.56,0.64,1)',
        'badge-pulse': 'badgePulse 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideDown: {
          from: { opacity: '0', transform: 'translateY(-8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        completePop: {
          '0%': { transform: 'scale(1)' },
          '40%': { transform: 'scale(1.35)' },
          '70%': { transform: 'scale(0.9)' },
          '100%': { transform: 'scale(1)' },
        },
        particleFly: {
          '0%': { opacity: '1', transform: 'translate(0,0) scale(1)' },
          '100%': { opacity: '0', transform: 'var(--fly-end) scale(0)' },
        },
        winCardIn: {
          '0%': { opacity: '0', transform: 'scale(0.8) translateY(10px)' },
          '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
        },
        badgePulse: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(212,164,58,0.4)' },
          '50%': { boxShadow: '0 0 0 6px rgba(212,164,58,0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
