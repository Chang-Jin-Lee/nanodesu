from scripts.fetch.rss import fetch_rss


def steam_news_url(appid):
    return f"https://store.steampowered.com/feeds/news/app/{appid}/"


def fetch_steam_news(appid, title, region="global", category="game"):
    url = steam_news_url(appid)
    source = f"steam-{appid}"
    items = fetch_rss(url, source=source, region=region, category=category)
    for item in items:
        item["watch_title_hint"] = title
    return items
