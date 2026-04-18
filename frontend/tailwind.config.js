/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        space: {
          950: '#020208',
          900: '#050510',
          800: '#0a0a1f',
          700: '#0f0f2e',
          600: '#14143d',
        },
        cyan: {
          glow: '#00d4ff',
        },
        red: {
          50:  '#fff0f0',
          100: '#ffd6d6',
          200: '#ffaaaa',
          300: '#ff6666',
          400: '#ff3333',
          500: '#ff1a1a',
          600: '#e60000',
          700: '#b30000',
          800: '#800000',
          900: '#4d0000',
          950: '#1a0000',
          glow: '#ff1a1a',
        },
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 212, 255, 0.3)',
        'glow-red':  '0 0 25px rgba(255, 26, 26, 0.5)',
        'glow-sm': '0 0 8px rgba(0, 212, 255, 0.2)',
        glass: '0 8px 32px rgba(0, 0, 0, 0.4)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        cursor: 'cursor 1s step-end infinite',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        cursor: { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0' } },
      },
    },
  },
  plugins: [],
}
