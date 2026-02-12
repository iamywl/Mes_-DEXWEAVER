import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    assetsDir: '',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:30461',
        changeOrigin: true,
      },
    },
  },
})
