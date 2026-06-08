import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/users': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/store': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/kiosks': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/kiosk_client': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/shelves': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/categories': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/products': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/order': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/dashboard': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
