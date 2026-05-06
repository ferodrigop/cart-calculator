import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CheckoutBreakdown } from "@/features/cart/schema";
import { formatCurrency } from "@/lib/format";

export function CheckoutSummary({ breakdown }: { breakdown: CheckoutBreakdown }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Checkout breakdown</CardTitle>
        <CardDescription>Server-computed totals.</CardDescription>
      </CardHeader>
      <CardContent>
        <dl className="divide-y divide-border">
          <Row label="Subtotal" value={breakdown.subtotal} />
          <Row label="Taxes" value={breakdown.taxes} />
          <Row label="Discount" value={breakdown.discount} negative />
          <Row label="Total" value={breakdown.total} emphasis />
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
}: {
  label: string;
  value: number;
  negative?: boolean;
  emphasis?: boolean;
}) {
  const formatted = formatCurrency(negative ? -Math.abs(value) : value);
  return (
    <div className="flex items-center justify-between py-2">
      <dt className={emphasis ? "text-base font-semibold" : "text-sm text-muted-foreground"}>
        {label}
      </dt>
      <dd
        className={
          emphasis
            ? "text-base font-semibold tabular-nums"
            : "text-sm tabular-nums"
        }
      >
        {formatted}
      </dd>
    </div>
  );
}
