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

export const CATEGORY_ACCENTS: Record<string, string> = {
  markets: "#2f6f52",
  business: "#8c5a2b",
  technology: "#5b5fa6",
  "us-news": "#2e6b8c",
  "world-news": "#1f8a8c",
  politics: "#6b4c8c",
  sports: "#a63d3d",
  "science-health": "#2e8c6b",
  culture: "#a6437a",
};

export function categoryName(slug: string): string {
  return CATEGORY_NAMES[slug] ?? slug;
}

export function categoryAccent(slug: string): string {
  return CATEGORY_ACCENTS[slug] ?? "#4a5578";
}
