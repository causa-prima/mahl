import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../Server/wwwroot',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5059',
    },
  },
  test: {
    environment: 'happy-dom',
    include: ['src/**/*.test.{ts,tsx}'],
    setupFiles: ['./src/test/setup.ts'],
    // Vitests Default sind 5 s. Unter der Systemlast eines Stryker-Laufs hat das einen Test,
    // der isoliert ~900 ms braucht, in den Timeout laufen lassen – ein falscher Rot-Alarm
    // ohne echten Regress. Diese Tests prüfen Verhalten, nicht Geschwindigkeit. Gleicher
    // Wert wie `additional-timeout` in stryker-config.json.
    testTimeout: 15000,
    // @mui/material 9.1.x macht in seinem .mjs-Build einen Directory-Import von
    // react-transition-group, der unter nativem Node-ESM scheitert. Inline-Transform
    // durch Vite löst den Import korrekt auf.
    server: { deps: { inline: ['@mui/material'] } },
  },
})
