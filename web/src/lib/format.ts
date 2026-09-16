// `new Date("2026-09-16")` parses as UTC midnight, which renders as the
// previous day in negative-UTC-offset timezones. Parse the parts directly
// so the date shown always matches the date the briefing is actually for.
export function formatBriefingDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}
