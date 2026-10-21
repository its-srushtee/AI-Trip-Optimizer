import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // `vite preview` serves the production build — same proxy rules, no HMR
  // websocket, so it works reliably inside an embedded preview iframe.
  preview: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/images': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // allow the live-preview proxy host (and any other host) to connect
    allowedHosts: true,
    // HMR over the preview proxy must use the standard TLS port
    // hmr: { clientPort: 443, protocol: 'wss' },
    // Proxy API + image requests to the FastAPI backend so the browser only
    // ever talks to one origin (works for local dev AND the live preview).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/images': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
