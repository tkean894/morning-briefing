export const CATEGORY_NAMES: Record<string, string> = {
  markets: "Markets & Economy",
  business: "Business",
  technology: "Technology",
  "us-news": "U.S. News",
  "world-news": "World News",
  politics: "Politics & Policy",
  sports: "Sports",
  "science-health": "Science & Health",
  culture: "Culture & Entertainment",
};

export const CATEGORY_COLORS: Record<string, string> = {
  markets: "bg-emerald-50 text-emerald-700",
  business: "bg-amber-50 text-amber-700",
  technology: "bg-violet-50 text-violet-700",
  "us-news": "bg-sky-50 text-sky-700",
  "world-news": "bg-cyan-50 text-cyan-700",
  politics: "bg-indigo-50 text-indigo-700",
  sports: "bg-orange-50 text-orange-700",
  "science-health": "bg-teal-50 text-teal-700",
  culture: "bg-pink-50 text-pink-700",
};

export function categoryName(slug: string): string {
  return CATEGORY_NAMES[slug] ?? slug;
}

export function categoryColor(slug: string): string {
  return CATEGORY_COLORS[slug] ?? "bg-neutral-100 text-neutral-700";
}
