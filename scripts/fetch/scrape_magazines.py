import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scripts.fetch.common import FetchError, fetch_url

SHONENJUMP_URL = "https://shonenjump.com/j/news/newsmore_rensai.html"
SHONENMAGAZINE_URL = "https://shonenmagazine.com/info/"
WEBSUNDAY_URL = "https://websunday.net/news/"

ENTRY_DATE_RE = re.compile(r"entry/(\d{4})(\d{2})(\d{2})")


def parse_shonenjump_html(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("li.newsList"):
        a = li.find("a", href=True)
        p = li.find("p")
        if not a or not p:
            continue

        time_tag = p.find("time")
        published = ""
        if time_tag:
            published = time_tag.get_text(strip=True).replace("/", "-")
            time_tag.extract()

        title = p.get_text(strip=True)
        if not title:
            continue

        items.append(
            {
                "title": title,
                "url": a["href"],
                "published": published,
                "source": "shonenjump",
                "region": "japan",
                "category": "manga",
                "summary": "",
            }
        )
    return items


def parse_shonenmagazine_html(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    container = soup.select_one(".info--article-main") or soup
    for block in container.select(".content"):
        a = block.find("a", class_="thumb", href=True)
        title_tag = block.find("div", class_="title")
        if not a or not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        if not title:
            continue

        url = a["href"]
        published = ""
        match = ENTRY_DATE_RE.search(url)
        if match:
            published = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        text_tag = block.find("div", class_="text")
        items.append(
            {
                "title": title,
                "url": url,
                "published": published,
                "source": "shonenmagazine",
                "region": "japan",
                "category": "manga",
                "summary": text_tag.get_text(strip=True) if text_tag else "",
            }
        )
    return items


def parse_websunday_html(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("li.p1s1-list-v__item"):
        a = li.find("a", href=True)
        title_tag = li.select_one(".p1s1-list-v__box02__title")
        date_tag = li.select_one(".p1s1-list-v__box02__date")
        if not a or not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        if not title:
            continue

        published = date_tag.get_text(strip=True).replace("/", "-") if date_tag else ""
        items.append(
            {
                "title": title,
                "url": urljoin(WEBSUNDAY_URL, a["href"]),
                "published": published,
                "source": "websunday",
                "region": "japan",
                "category": "manga",
                "summary": "",
            }
        )
    return items


def fetch_all_magazines():
    """Collect items from every magazine site that responds.

    Each site is fetched independently: one site being down or having
    changed its markup must not cost us the others. Sites that fail are
    skipped, and `fetch_all.py` records the source-level status — a partial
    result is more useful here than none.

    If every site fails, though, that is a real outage and must not look
    like a quiet, legitimate zero-item run: we raise so `fetch_all.py`
    records `ok: False` with the underlying errors. A site that succeeds
    and simply has no news today is not a failure and must not raise.
    """
    sites = (
        (SHONENJUMP_URL, parse_shonenjump_html),
        (SHONENMAGAZINE_URL, parse_shonenmagazine_html),
        (WEBSUNDAY_URL, parse_websunday_html),
    )
    results = []
    failures = []
    for url, parser in sites:
        try:
            results.extend(parser(fetch_url(url)))
        except Exception as exc:
            failures.append(f"{url}: {exc!r}")

    if len(failures) == len(sites):
        raise FetchError(
            f"all {len(sites)} magazine sites failed: " + "; ".join(failures)
        )

    return results
