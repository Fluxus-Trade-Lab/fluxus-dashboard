import { defineConfig } from 'vitest/config'

export default defineConfig({
  // The app is built by vite.config.js with @vitejs/plugin-react; this file is
  // a separate config, so without this the tests transform JSX with esbuild's
  // classic runtime and every component render throws "React is not defined".
  // @testing-library/react was installed and never exercised, so nothing caught
  // it until the first test that rendered a provider.
  esbuild: { jsx: 'automatic' },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.js'],
    globals: true,
  },
})
