import { z } from "zod";

export const cartItemSchema = z.object({
  name: z.string().min(1, "Required"),
  unit_price: z.coerce.number().positive("Must be > 0"),
  quantity: z.coerce.number().int("Must be whole").positive("Must be > 0"),
});

export const cartSchema = z.object({
  items: z.array(cartItemSchema).min(1, "Add at least one item"),
});

export type CartInput = z.input<typeof cartSchema>;
export type CartValues = z.output<typeof cartSchema>;

export type CheckoutBreakdown = {
  subtotal: number;
  taxes: number;
  discount: number;
  total: number;
};
