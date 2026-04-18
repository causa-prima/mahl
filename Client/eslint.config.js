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

      // throw ist in exhaustive-switch-Handlern (default: never) und für echte technische
      // Ausnahmezustände (5xx, Netzwerk) erlaubt. functional/no-throw-statements ist zu
      // aggressiv: es würde auch `throw new Error(...)` in default-never-Zweigen blockieren,
      // die für strukturelle Vollständigkeit nötig sind. Enforcement via Review-Checkliste.
      'functional/no-throw-statements': 'off',
    },
  },

  // --- ROP: neverthrow-Shortcuts verboten (außer in Tests) ---
  // .isOk() / .isErr() sind partielle Checks – stattdessen .match(ok, err) verwenden.
  // ._unsafeUnwrap() ist ein expliziter Laufzeit-Fehler-Auslöser – nur in Tests erlaubt.
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: ['src/**/*.test.{ts,tsx}', 'src/**/*.spec.{ts,tsx}'],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector: "MemberExpression[property.name='isOk']",
          message: "isOk() nicht verwenden. Stattdessen .match(ok => ..., err => ...) (neverthrow) nutzen. Siehe CODING_GUIDELINE_TYPESCRIPT.md Abschnitt 4.",
        },
        {
          selector: "MemberExpression[property.name='isErr']",
          message: "isErr() nicht verwenden. Stattdessen .match(ok => ..., err => ...) (neverthrow) nutzen. Siehe CODING_GUIDELINE_TYPESCRIPT.md Abschnitt 4.",
        },
        {
          selector: "MemberExpression[property.name='_unsafeUnwrap']",
          message: "_unsafeUnwrap() ist nur in Tests erlaubt. Im Produktionscode .match(ok => ..., err => ...) verwenden.",
        },
      ],
    },
  },

  // --- fetch() verboten außerhalb von src/services/ ---
  // API-Calls gehören ausschließlich in src/services/, nicht in Komponenten, Pages oder Hooks.
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: ['src/services/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector: "CallExpression[callee.name='fetch']",
          message: "fetch() nicht direkt verwenden. API-Calls gehören ausschließlich in src/services/.",
        },
      ],
    },
  },

  // --- React Query: Wrapper-Pflicht ---
  // useQuery/useMutation nie direkt verwenden – stattdessen useResultQuery/useResultMutation.
  // Ausnahme: die Wrapper-Dateien selbst dürfen direkt importieren.
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: [
      'src/hooks/useResultQuery.ts',
      'src/hooks/useResultMutation.ts',
    ],
    rules: {
      '@typescript-eslint/no-restricted-imports': [
        'error',
        {
          paths: [
            {
              name: '@tanstack/react-query',
              importNames: ['useQuery', 'useMutation'],
              message: "useQuery/useMutation nicht direkt verwenden. Stattdessen useResultQuery/useResultMutation aus src/hooks/ nutzen. Siehe CODING_GUIDELINE_TYPESCRIPT.md Abschnitt 4b.",
            },
          ],
        },
      ],
    },
  },
])
