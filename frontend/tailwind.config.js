/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        risk: {
          low: '#10B981',      // Emerald 500
          moderate: '#F59E0B', // Amber 500
          high: '#F97316',     // Orange 500
          severe: '#EF4444',   // Red 500
        },
        brand: {
          50: '#F0F4F8',
          100: '#D9E2EC',
          500: '#182B49',
          600: '#102038',
          700: '#0B1526',
        }
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
