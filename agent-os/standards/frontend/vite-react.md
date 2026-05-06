# Vite + React + TypeScript Standards

Conventions for the bonus frontend in `frontend/`.

1. **Strict TypeScript from day one.** In `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "strict": true,
       "noUncheckedIndexedAccess": true,
       "noImplicitOverride": true,
       "noFallthroughCasesInSwitch": true,
       "noEmit": true
     }
   }
   ```
   Run `tsc --noEmit` in CI as a separate step from `vite build`.
2. **Absolute imports configured in both places.** In `tsconfig.json`:
   `"baseUrl": "./src", "paths": { "@/*": ["./*"] }`. In `vite.config.ts`:
   `resolve.alias: { "@": path.resolve(__dirname, "./src") }`. Doing only one breaks
   either the IDE or the build.
3. **Env vars only via `import.meta.env.VITE_*`.** Declare them in `src/vite-env.d.ts`
   with an `ImportMetaEnv` interface so they're typed. Never read non-`VITE_`-prefixed
   vars (Vite won't expose them). Never hardcode the API base URL.
4. **TanStack Query for server state.** Single `QueryClient` at module scope (not inside
   a component). Wrap the app in `<QueryClientProvider>`. Define query keys as typed
   factories (`checkoutKeys.detail(id)`) in `src/lib/queryKeys.ts` to prevent
   stringly-typed cache invalidation bugs.
5. **Centralized API client, feature-co-located hooks.** API client in `src/lib/api.ts`
   (typed `fetch` wrapper or `ky`/`axios` instance with JWT attached via interceptor).
   Query/mutation hooks live next to their feature, e.g.
   `src/features/checkout/useCheckout.ts` — never in a global `hooks/` dump.
