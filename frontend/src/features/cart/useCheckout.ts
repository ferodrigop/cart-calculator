import { useMutation } from "@tanstack/react-query";

import type { CartValues, CheckoutBreakdown } from "@/features/cart/schema";
import { apiFetch } from "@/lib/api";

export function useCheckout() {
  return useMutation({
    mutationFn: (values: CartValues) =>
      apiFetch<CheckoutBreakdown>("/checkout", { method: "POST", body: values }),
  });
}
