// All amounts in the app are USD (a US immigration practice) -- shown with
// a currency symbol so a bare number never gets mistaken for something
// else (a count, a percentage) in the billing and reports views.
export function formatMoney(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}
