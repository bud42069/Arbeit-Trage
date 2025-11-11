/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './public/index.html',
  ],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        'app-bg': '#0B0F14',
        'surface': {
          1: '#0F141A',
          2: '#121923',
          3: '#17202A',
        },
        // Text
        'text': {
          primary: '#E5EDF5',
          secondary: '#B6C2CF',
          tertiary: '#7C8AA0',
          muted: '#5A6B7D',
        },
        // Borders
        'border': {
          subtle: '#1E2937',
          strong: '#223043',
        },
        // Lime accent
        'lime': {
          400: '#A3E635',
          500: '#84CC16',
          700: '#4D7C0F',
        },
        // Status
        'success': '#22C55E',
        'warning': '#F59E0B',
        'danger': '#EF4444',
        'info': '#60A5FA',
        // Trading
        'buy': '#22C55E',
        'sell': '#F43F5E',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      fontSize: {
        'xs': '12px',
        'sm': '14px',
        'base': '16px',
        'lg': '18px',
        'xl': '20px',
        '2xl': '24px',
        '3xl': '28px',
      },
      boxShadow: {
        'elevation-1': '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        'elevation-2': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        'focus': '0 0 0 2px rgba(163, 230, 53, 0.6)',
      },
      animation: {
        'pulse-lime': 'pulse-lime 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        'pulse-lime': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
    },
  },
  plugins: [],
}
