import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CheckoutBreakdown } from "@/features/cart/schema";
import { formatCurrency } from "@/lib/format";

export function CheckoutSummary({
  breakdown,
  isPending = false,
}: {
  breakdown: CheckoutBreakdown | null;
  isPending?: boolean;
}) {
  return (
    <Card aria-busy={isPending} aria-live="polite">
      <CardHeader>
        <CardTitle>Checkout breakdown</CardTitle>
        <CardDescription>
          {isPending && !breakdown ? "Calculating…" : "Server-computed totals."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="divide-y divide-border">
          <Row label="Subtotal" value={breakdown?.subtotal} pending={isPending} />
          <Row label="Taxes" value={breakdown?.taxes} pending={isPending} />
          <Row label="Discount" value={breakdown?.discount} negative pending={isPending} />
          <Row label="Total" value={breakdown?.total} emphasis pending={isPending} />
        </dl>
      </CardContent>
    </Card>
  );
}

function Row({
  label,
  value,
  negative = false,
  emphasis = false,
  pending = false,
}: {
  label: string;
  value: number | undefined;
  negative?: boolean;
  emphasis?: boolean;
  pending?: boolean;
}) {
  // Render `$0.00` (not `-$0.00`) when discount is exactly zero.
  const signed = negative && value !== undefined && Math.abs(value) > 0 ? -Math.abs(value) : value;
  return (
    <div className="flex items-center justify-between py-2">
      <dt className={emphasis ? "text-base font-semibold" : "text-sm text-muted-foreground"}>
        {label}
      </dt>
      {value === undefined ? (
        <dd className="h-4 w-16 animate-pulse rounded bg-muted" aria-hidden={!pending} />
      ) : (
        <dd
          className={
            emphasis
              ? "text-base font-semibold tabular-nums"
              : "text-sm tabular-nums"
          }
        >
          {formatCurrency(signed as number)}
        </dd>
      )}
    </div>
  );
}
