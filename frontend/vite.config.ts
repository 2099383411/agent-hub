import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 8201,
    proxy: {
      '/api': { target: 'http://backend:8200', changeOrigin: true },
      '/mcp': { target: 'http://backend:8200', ws: true },
    },
  },
});
