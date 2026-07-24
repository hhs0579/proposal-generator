import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/products': 'http://localhost:8000',
      '/generate': 'http://localhost:8000',
      '/save': 'http://localhost:8000',
      '/load': 'http://localhost:8000'
    }
  }
})
