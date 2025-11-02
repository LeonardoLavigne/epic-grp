/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f2fbf7',
          100: '#e6f7ef',
          200: '#cfeee0',
          300: '#b3e2cd',
          400: '#8fd2b3',
          500: '#6cc39b',
          600: '#4aa882',
          700: '#3a866a',
          800: '#2f6955',
          900: '#285647',
        },
        ink: '#1f2937',
        surface: '#ffffff',
        mist: '#f6f8fb',
        accent: {
          100: '#fde2e4', // peach
          200: '#e2ece9', // mint
          300: '#e9e2f8', // lavender
          400: '#d7eef7', // sky
        },
      },
      boxShadow: {
        soft: '0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.06)',
      },
      borderRadius: {
        xl: '0.9rem',
      },
    },
  },
  plugins: [],
}
