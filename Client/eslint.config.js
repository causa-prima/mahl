import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import functional from 'eslint-plugin-functional'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.strictTypeChecked,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      functional.configs.recommended,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      'prefer-const': 'error',
      'no-var': 'error',
      'no-param-reassign': 'error',

      // Exhaustive switch/if on discriminated unions – pflicht für Sum-Type-Pattern
      '@typescript-eslint/switch-exhaustiveness-check': 'error',
      // Readonly class properties where possible
      '@typescript-eslint/prefer-readonly': 'error',

      // --- functional/recommended Overrides ---

      // Category 1 – technischer React-Zwang: Hooks und Rendering sind inherent side-effectful.
      // useEffect, dispatch, createRoot().render() etc. sind Expression Statements by design.
      'functional/no-expression-statements': 'off',

      // Category 1 – Event-Handler in React geben void zurück. Das ist kein Smell,
      // sondern der React-Vertrag für onClick/onChange etc.
      'functional/no-return-void': 'off',

      // Category 1 – Parameterlose Komponenten und Hooks sind valide React-Patterns.
      // `const Spinner = () => <div />` soll erlaubt sein.
      'functional/functional-parameters': 'off',
    },
  },
  {
    files: ['src/components/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector: "CallExpression[callee.name='fetch']",
          message: "fetch() nicht direkt in Komponenten verwenden. API-Calls gehören in src/services/.",
        },
      ],
    },
  },
])
