/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.py',
    './static/js/**/*.js',
  ],
  safelist: [
    'bg-black/10',
    'bg-black/20',
    'bg-black/30',
    'bg-black/40',
    'bg-black/50',
    'bg-black/60',
    'bg-black/70',
    'bg-black/80',
    'bg-black/90',
  ],
  theme: {
    extend: {
      colors: {
        ink: 'rgb(var(--color-ink-rgb, 25 37 59) / <alpha-value>)',
        coral: 'rgb(var(--color-coral-rgb, 255 107 77) / <alpha-value>)',
        butter: 'rgb(var(--color-butter-rgb, 246 198 77) / <alpha-value>)',
        cream: 'rgb(var(--color-cream-rgb, 255 250 242) / <alpha-value>)',
        mint: '#e6f0e8',
        softmint: '#7ac9b3',
        peach: '#f7c9bd',
        sky: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
          DEFAULT: '#b8deeb',
        },
        lavender: '#ded8f4',
        muted: '#827f78',
      },
      fontFamily: {
        sans: ['DM Sans', 'sans-serif'],
        display: ['Fraunces', 'serif'],
        inter: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        toy: '0 10px 25px rgba(25,37,59,.11)',
        button: '0 7px 0 var(--color-coral-dark, #df543d), 0 11px 18px rgba(0,0,0,.16)',
      },
    },
  },
  plugins: [],
}
