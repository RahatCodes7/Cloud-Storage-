import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/s/': 'http://localhost:8000',
    },
  },
  define: {
    // Make API URL configurable — set VITE_API_URL on Vercel
    // Defaults to empty (same-origin proxy) for local dev
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || ''),
  },
})
