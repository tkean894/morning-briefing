"""Static definition of the interest taxonomy, seeded into the `interests`
table by alembic migration 0002. Edit here, then create a follow-up data
migration if it needs to change later."""

TAXONOMY: list[dict] = [
    {
        "slug": "markets",
        "name": "Markets & Economy",
        "children": [
            {"slug": "markets-stocks", "name": "Stocks"},
            {"slug": "markets-macro", "name": "Macroeconomics"},
            {"slug": "markets-crypto", "name": "Crypto"},
            {"slug": "markets-personal-finance", "name": "Personal Finance"},
        ],
    },
    {
        "slug": "business",
        "name": "Business",
        "children": [
            {"slug": "business-earnings", "name": "Earnings"},
            {"slug": "business-ma", "name": "M&A"},
            {"slug": "business-startups", "name": "Startups"},
            {"slug": "business-major-companies", "name": "Major Companies"},
            {"slug": "business-careers", "name": "Careers"},
        ],
    },
    {
        "slug": "technology",
        "name": "Technology",
        "children": [
            {"slug": "technology-ai", "name": "AI"},
            {"slug": "technology-cybersecurity", "name": "Cybersecurity"},
            {"slug": "technology-consumer-tech", "name": "Consumer Technology"},
            {"slug": "technology-startups", "name": "Startups"},
        ],
    },
    {"slug": "us-news", "name": "U.S. News", "children": []},
    {"slug": "world-news", "name": "World News", "children": []},
    {"slug": "politics", "name": "Politics & Policy", "children": []},
    {
        "slug": "sports",
        "name": "Sports",
        "children": [
            {"slug": "sports-nfl", "name": "NFL"},
            {"slug": "sports-nba", "name": "NBA"},
            {"slug": "sports-mlb", "name": "MLB"},
            {"slug": "sports-nhl", "name": "NHL"},
            {"slug": "sports-college-football", "name": "College Football"},
            {"slug": "sports-college-basketball", "name": "College Basketball"},
            {"slug": "sports-soccer", "name": "Soccer"},
        ],
    },
    {"slug": "science-health", "name": "Science & Health", "children": []},
    {"slug": "culture", "name": "Culture & Entertainment", "children": []},
]

# category slug -> [(subcategory slug, name), ...], for prompting the LLM
# during story generation and for validating its answer.
SUBCATEGORIES_BY_CATEGORY: dict[str, list[tuple[str, str]]] = {
    parent["slug"]: [(c["slug"], c["name"]) for c in parent["children"]]
    for parent in TAXONOMY
}
