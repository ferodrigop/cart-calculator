# Tasks

## Deps & primitives

- [ ] Install runtime deps: `react-router-dom`, `@tanstack/react-query`,
      `react-hook-form`, `@hookform/resolvers`, `zod`, `lucide-react`,
      `sonner`.
- [ ] Add shadcn primitives via CLI: `button`, `input`, `label`, `form`,
      `card`, `table`, `sonner`.

## Plumbing

- [ ] `src/lib/queryClient.ts` — module-scope `QueryClient`.
- [ ] `src/lib/queryKeys.ts` — typed key factories.
- [ ] `src/lib/auth.ts` — token store + listeners.
- [ ] `src/lib/api.ts` — `apiFetch<T>` with bearer + 401 refresh.
- [ ] `src/vite-env.d.ts` — typed `VITE_API_BASE_URL`.
- [ ] `frontend/.env.example`.

## Routing

- [ ] `src/routes.tsx` — `<RootRedirect>`, `<RequireAuth>`, four routes.
- [ ] `src/App.tsx` — providers + `<RouterProvider>` + `<Toaster>`.

## Auth feature

- [ ] `src/features/auth/loginSchema.ts`, `registerSchema.ts`.
- [ ] `src/features/auth/useLogin.ts`, `useRegister.ts`.
- [ ] `src/features/auth/LoginPage.tsx`.
- [ ] `src/features/auth/RegisterPage.tsx`.

## Cart feature

- [ ] `src/features/cart/cartSchema.ts`.
- [ ] `src/features/cart/useCheckout.ts`.
- [ ] `src/features/cart/CheckoutSummary.tsx`.
- [ ] `src/features/cart/CartPage.tsx`.

## Verify

- [ ] `cd frontend && npx tsc --noEmit`.
- [ ] `cd frontend && npm run build`.
- [ ] `cd frontend && npm run dev` — `/` boots clean, redirects to `/login`.

## Ship

- [ ] `git commit -m "feat: frontend SPA"`.
- [ ] `git push -u origin feat/frontend`.
- [ ] `gh pr create --base main --title "feat: frontend SPA"`.
