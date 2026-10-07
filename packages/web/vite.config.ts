import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:3000',
      // Demo-only "you have mail" surface (scripts/dev-mailbox.mjs). The
      // mailbox routes on /inbox and /, so strip the /mailbox mount prefix.
      '/mailbox': {
        target: 'http://127.0.0.1:4000',
        rewrite: (path) => path.replace(/^\/mailbox/, ''),
      },
    },
  },
});