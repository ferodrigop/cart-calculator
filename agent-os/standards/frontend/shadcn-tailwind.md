# shadcn/ui + Tailwind Standards

Conventions for UI components and styling.

1. **Install via the unified CLI.** Run `npx shadcn@latest init`, commit
   `components.json`, and add components on demand:
   `npx shadcn@latest add button form input dialog card`. Treat files in
   `src/components/ui/` as **your code** — edit them freely, not as vendored deps.
2. **Theme via CSS custom properties.** All theme tokens live in `src/index.css` under
   `:root` and `.dark` (e.g. `--background`, `--primary`, `--ring`). In components,
   reference them through Tailwind: `bg-background text-foreground`. Never hardcode hex
   colors in components.
3. **Forms = shadcn `<Form>` + react-hook-form + zod.** Define a Zod schema, e.g.
   ```ts
   const checkoutSchema = z.object({
     items: z.array(z.object({
       name: z.string().min(1),
       unit_price: z.number().positive(),
       quantity: z.number().int().positive(),
     })).min(1),
   });
   ```
   Pass `zodResolver(checkoutSchema)` to `useForm`. Wrap fields in `<FormField>` /
   `<FormControl>` / `<FormMessage>` so validation errors render automatically.
4. **Compose, don't fork.** Build feature components (`<CheckoutItemRow>`,
   `<CheckoutSummary>`) by composing primitives from `components/ui/`. If a primitive
   needs a project-wide change, edit the file in `components/ui/` directly — never wrap
   it just to tweak styles.
5. **Use the generated `cn()` helper.** `clsx` + `tailwind-merge` via `cn()` in
   `src/lib/utils.ts` for every conditional className:
   `cn("px-4", isActive && "bg-primary", className)`. Configure Tailwind's `content` glob
   to include `./src/**/*.{ts,tsx}` so unused styles tree-shake.
