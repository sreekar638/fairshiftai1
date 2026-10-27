/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#142B4A',
          dark: '#0D1E34',
          light: '#1E3E68',
        },
        teal: {
          DEFAULT: '#0F9D8A',
          dark: '#0B7A6B',
          light: '#E6F7F5',
        },
        surface: '#FFFFFF',
        canvas: '#F5F7FA',
        main: '#172B4D',
        secondary: '#64748B',
        warning: '#D97706',
        critical: '#DC2626',
        border: '#E2E8F0',
      },
    },
  },
  plugins: [],
}
