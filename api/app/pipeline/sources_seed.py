"""Static list of ingestion sources, seeded into the `sources` table by
alembic migration 0004. RSS feed URLs were verified reachable at the time
this was written -- feeds do rot, so expect to prune/replace dead ones.

credibility_tier: 1 = wire service / major broadcaster, 2 = reputable
specialist or mainstream outlet. Used later during story ranking.
"""

SOURCES: list[dict] = [
    # Markets & Economy
    {
        "slug": "cnbc-finance",
        "name": "CNBC Finance",
        "kind": "rss",
        "category": "markets",
        "feed_url": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "credibility_tier": 2,
    },
    {
        "slug": "marketwatch-top",
        "name": "MarketWatch Top Stories",
        "kind": "rss",
        "category": "markets",
        "feed_url": "https://www.marketwatch.com/rss/topstories",
        "credibility_tier": 2,
    },
    # Business
    {
        "slug": "fortune",
        "name": "Fortune",
        "kind": "rss",
        "category": "business",
        "feed_url": "https://fortune.com/feed/",
        "credibility_tier": 2,
    },
    {
        "slug": "axios",
        "name": "Axios",
        "kind": "rss",
        "category": "business",
        "feed_url": "https://www.axios.com/feeds/feed.rss",
        "credibility_tier": 2,
    },
    # Technology
    {
        "slug": "techcrunch",
        "name": "TechCrunch",
        "kind": "rss",
        "category": "technology",
        "feed_url": "https://techcrunch.com/feed/",
        "credibility_tier": 2,
    },
    {
        "slug": "ars-technica",
        "name": "Ars Technica",
        "kind": "rss",
        "category": "technology",
        "feed_url": "https://feeds.arstechnica.com/arstechnica/index",
        "credibility_tier": 2,
    },
    {
        "slug": "the-verge",
        "name": "The Verge",
        "kind": "rss",
        "category": "technology",
        "feed_url": "https://www.theverge.com/rss/index.xml",
        "credibility_tier": 2,
    },
    {
        "slug": "wired",
        "name": "Wired",
        "kind": "rss",
        "category": "technology",
        "feed_url": "https://www.wired.com/feed/rss",
        "credibility_tier": 2,
    },
    # U.S. News
    {
        "slug": "npr-news",
        "name": "NPR News",
        "kind": "rss",
        "category": "us-news",
        "feed_url": "https://feeds.npr.org/1001/rss.xml",
        "credibility_tier": 1,
    },
    {
        "slug": "bbc-us-canada",
        "name": "BBC US & Canada",
        "kind": "rss",
        "category": "us-news",
        "feed_url": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
        "credibility_tier": 1,
    },
    # World News
    {
        "slug": "bbc-world",
        "name": "BBC World",
        "kind": "rss",
        "category": "world-news",
        "feed_url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "credibility_tier": 1,
    },
    {
        "slug": "npr-world",
        "name": "NPR World",
        "kind": "rss",
        "category": "world-news",
        "feed_url": "https://feeds.npr.org/1004/rss.xml",
        "credibility_tier": 1,
    },
    # Politics & Policy
    {
        "slug": "npr-politics",
        "name": "NPR Politics",
        "kind": "rss",
        "category": "politics",
        "feed_url": "https://feeds.npr.org/1014/rss.xml",
        "credibility_tier": 1,
    },
    {
        "slug": "politico",
        "name": "Politico",
        "kind": "rss",
        "category": "politics",
        "feed_url": "https://rss.politico.com/politics-news.xml",
        "credibility_tier": 2,
    },
    # Sports
    {
        "slug": "espn",
        "name": "ESPN",
        "kind": "rss",
        "category": "sports",
        "feed_url": "https://www.espn.com/espn/rss/news",
        "credibility_tier": 2,
    },
    {
        "slug": "cbs-sports",
        "name": "CBS Sports",
        "kind": "rss",
        "category": "sports",
        "feed_url": "https://www.cbssports.com/rss/headlines/",
        "credibility_tier": 2,
    },
    {
        "slug": "bbc-sport",
        "name": "BBC Sport",
        "kind": "rss",
        "category": "sports",
        "feed_url": "http://feeds.bbci.co.uk/sport/rss.xml",
        "credibility_tier": 1,
    },
    # Science & Health
    {
        "slug": "npr-science",
        "name": "NPR Science",
        "kind": "rss",
        "category": "science-health",
        "feed_url": "https://feeds.npr.org/1007/rss.xml",
        "credibility_tier": 1,
    },
    {
        "slug": "npr-health",
        "name": "NPR Health",
        "kind": "rss",
        "category": "science-health",
        "feed_url": "https://feeds.npr.org/1128/rss.xml",
        "credibility_tier": 1,
    },
    {
        "slug": "science-daily",
        "name": "Science Daily",
        "kind": "rss",
        "category": "science-health",
        "feed_url": "https://www.sciencedaily.com/rss/all.xml",
        "credibility_tier": 2,
    },
    # Culture & Entertainment
    {
        "slug": "npr-arts-life",
        "name": "NPR Arts & Life",
        "kind": "rss",
        "category": "culture",
        "feed_url": "https://feeds.npr.org/1008/rss.xml",
        "credibility_tier": 1,
    },
    {
        "slug": "variety",
        "name": "Variety",
        "kind": "rss",
        "category": "culture",
        "feed_url": "https://variety.com/feed/",
        "credibility_tier": 2,
    },
    # API-based sources -- only run if the corresponding API key is set.
    {
        "slug": "guardian",
        "name": "The Guardian",
        "kind": "api_guardian",
        "category": "world-news",
        "feed_url": None,
        "credibility_tier": 1,
    },
    {
        "slug": "nyt",
        "name": "The New York Times",
        "kind": "api_nyt",
        "category": "us-news",
        "feed_url": None,
        "credibility_tier": 1,
    },
]
