import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: the FastAPI backend runs on :8010; proxying /api keeps the session cookie same-origin.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8010' } },
})
