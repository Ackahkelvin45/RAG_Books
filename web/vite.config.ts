import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: the FastAPI backend runs on :8010; proxying /api keeps the session cookie same-origin.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': 'http://127.0.0.1:8010' } },
  // Without this the minifier writes media queries as `(width<=760px)`, which iOS 15 and older
  // Android browsers ignore entirely - those phones would get the desktop layout.
  build: { cssTarget: ['safari14', 'chrome87', 'firefox78'] },
})
