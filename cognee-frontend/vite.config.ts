import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// For Vitest specific types, you might need:
// import type { UserConfig as VitestUserConfigInterface } from 'vitest/config';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom', // Using jsdom due to happy-dom Node version warning
    setupFiles: './src/setupTests.ts',
    css: true, // If you want to process CSS during tests (e.g. for CSS Modules)
  },
});
