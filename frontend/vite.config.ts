import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // SSE endpoint - requires special timeout configuration
      '/api/v1/events/stream': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Disable timeout for SSE (long-lived connection)
        timeout: 0,
        configure: (proxy) => {
          // Set 1 hour timeout for SSE connections
          proxy.on('proxyReq', (_proxyReq, _req, res) => {
            // Disable buffering for real-time streaming
            res.setHeader('X-Accel-Buffering', 'no');
          });
          // Keep connection alive
          proxy.on('open', () => {
            // Connection opened - SSE stream started
          });
        },
      },
      // Standard API endpoints
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        timeout: 120000, // 2 minutes for regular API calls
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
