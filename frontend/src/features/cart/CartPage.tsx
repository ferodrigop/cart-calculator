import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { useMemo } from "react";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CheckoutSummary } from "@/features/cart/CheckoutSummary";
import { type CartInput, type CartValues, cartSchema } from "@/features/cart/schema";
import { useCheckout } from "@/features/cart/useCheckout";
import { ApiError } from "@/lib/api";
import { clearTokens } from "@/lib/auth";
import { formatCurrency } from "@/lib/format";

const blankItem = { name: "", unit_price: 0, quantity: 1 };

export function CartPage() {
  const navigate = useNavigate();
  const checkout = useCheckout();

  const form = useForm<CartInput, unknown, CartValues>({
    resolver: zodResolver(cartSchema),
    defaultValues: { items: [{ ...blankItem }] },
    mode: "onBlur",
  });

  const { fields, append, remove } = useFieldArray({ control: form.control, name: "items" });

  const watchedItems = useWatch({ control: form.control, name: "items" });
  const previewSubtotal = useMemo(() => {
    if (!watchedItems) return 0;
    return watchedItems.reduce((sum, row) => {
      const price = Number(row?.unit_price);
      const qty = Number(row?.quantity);
      if (!Number.isFinite(price) || !Number.isFinite(qty)) return sum;
      return sum + price * qty;
    }, 0);
  }, [watchedItems]);

  const onSubmit = (values: CartValues) => {
    checkout.mutate(values, {
      onSuccess: (breakdown) => {
        toast.success(`Total: ${formatCurrency(breakdown.total)}`);
      },
      onError: (error) => {
        const message =
          error instanceof ApiError && error.status === 401
            ? "Session expired. Please sign in again."
            : error instanceof Error
              ? error.message
              : "Checkout failed.";
        toast.error(message);
      },
    });
  };

  const onLogout = () => {
    clearTokens();
    navigate("/login", { replace: true });
  };

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container flex items-center justify-between py-4">
          <h1 className="text-lg font-semibold tracking-tight">cart-calculator</h1>
          <Button variant="ghost" size="sm" onClick={onLogout}>
            Sign out
          </Button>
        </div>
      </header>

      <div className="container grid gap-6 py-8 lg:grid-cols-[minmax(0,1fr)_360px]">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle>Your cart</CardTitle>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => append({ ...blankItem })}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add item
            </Button>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form id="cart-form" onSubmit={form.handleSubmit(onSubmit)} noValidate>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead className="w-32">Unit price</TableHead>
                      <TableHead className="w-24">Qty</TableHead>
                      <TableHead className="w-32 text-right">Line</TableHead>
                      <TableHead className="w-12" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fields.map((field, index) => {
                      const row = watchedItems?.[index];
                      const price = Number(row?.unit_price);
                      const qty = Number(row?.quantity);
                      const line =
                        Number.isFinite(price) && Number.isFinite(qty) ? price * qty : 0;
                      return (
                        <TableRow key={field.id}>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`items.${index}.name` as const}
                              render={({ field: f }) => (
                                <FormItem>
                                  <FormControl>
                                    <Input placeholder="Item name" {...f} />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`items.${index}.unit_price` as const}
                              render={({ field: f }) => (
                                <FormItem>
                                  <FormControl>
                                    <Input
                                      type="number"
                                      inputMode="decimal"
                                      step="0.01"
                                      min="0"
                                      {...f}
                                      value={(f.value ?? "") as string | number}
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`items.${index}.quantity` as const}
                              render={({ field: f }) => (
                                <FormItem>
                                  <FormControl>
                                    <Input
                                      type="number"
                                      inputMode="numeric"
                                      step="1"
                                      min="1"
                                      {...f}
                                      value={(f.value ?? "") as string | number}
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            {formatCurrency(line)}
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => remove(index)}
                              disabled={fields.length === 1}
                              aria-label={`Remove item ${index + 1}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
                {form.formState.errors.items?.root?.message && (
                  <p className="mt-2 text-sm font-medium text-destructive">
                    {form.formState.errors.items.root.message}
                  </p>
                )}
              </form>
            </Form>
          </CardContent>
        </Card>

        <aside className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Preview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-baseline justify-between">
                <span className="text-sm text-muted-foreground">Subtotal (client)</span>
                <span className="text-lg font-semibold tabular-nums">
                  {formatCurrency(previewSubtotal)}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                Taxes and discounts are computed on the server.
              </p>
              <Button
                type="submit"
                form="cart-form"
                className="w-full"
                disabled={checkout.isPending}
              >
                {checkout.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Submit checkout
              </Button>
            </CardContent>
          </Card>

          {(checkout.data || checkout.isPending) && (
            <CheckoutSummary
              breakdown={checkout.data ?? null}
              isPending={checkout.isPending}
            />
          )}
        </aside>
      </div>
    </main>
  );
}
