import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  assetsInclude: ["**/*.png"],
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/config': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        // Only proxied when the Python frontend_server is running locally
        configure: (proxy) => {
          proxy.on('error', () => {});
        }
      }
    }
  }
});