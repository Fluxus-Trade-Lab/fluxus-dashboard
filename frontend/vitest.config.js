import { defineConfig } from 'vitest/config'

export default defineConfig({
  // Match the app's JSX runtime (vite.config.js gets this from @vitejs/plugin-react)
  // so component tests can render .jsx without importing React.
  esbuild: { jsx: 'automatic' },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.js'],
    globals: true,
  },
})
