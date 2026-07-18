import re

from bs4 import BeautifulSoup

from scripts.fetch.common import fetch_url

COLLABOCAFE_URL = "https://collabo-cafe.com/"

DATE_RANGE_RE = re.compile(
    r"期間\s*[:：]\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*[〜~]\s*(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日"
)
DATE_OPEN_RE = re.compile(r"期間\s*[:：]\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*[〜~]\s*$")
DATE_DEADLINE_RE = re.compile(r"[〜~～]\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*まで")
VENUE_RE = re.compile(r"\bin\s+(\S+)")


def _iso(year, month, day):
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def parse_event_period(text):
    if not text:
        return None, None

    match = DATE_RANGE_RE.search(text)
    if match:
        start_year, start_month, start_day, end_year_explicit, end_month, end_day = match.groups()
        start = _iso(start_year, start_month, start_day)
        end_year = end_year_explicit or start_year
        if not end_year_explicit and int(end_month) < int(start_month):
            end_year = str(int(start_year) + 1)
        end = _iso(end_year, end_month, end_day)
        return start, end

    match = DATE_OPEN_RE.search(text)
    if match:
        year, month, day = match.groups()
        return _iso(year, month, day), None

    match = DATE_DEADLINE_RE.search(text)
    if match:
        year, month, day = match.groups()
        return None, _iso(year, month, day)

    return None, None


def parse_venue(title):
    match = VENUE_RE.search(title)
    return match.group(1) if match else ""


def parse_collabocafe_html(html):
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for article in soup.select("article.post-list"):
        link = article.find("a", href=True)
        if not link:
            continue

        title_tag = article.find("h1", class_="entry-title")
        title = title_tag.get_text(strip=True) if title_tag else link.get("title", "").strip()
        if not title:
            continue

        period_tag = article.select_one(".event-date, .event-icon")
        period_text = period_tag.get_text(strip=True) if period_tag else ""
        start_date, end_date = parse_event_period(period_text)

        category_tag = article.select_one(".cat-name")
        description_tag = article.select_one(".description")

        events.append(
            {
                "title": title,
                "url": link["href"],
                "venue": parse_venue(title),
                "start_date": start_date,
                "end_date": end_date,
                "category": category_tag.get_text(strip=True) if category_tag else "",
                "description": description_tag.get_text(strip=True) if description_tag else "",
                "source_site": "collabocafe",
            }
        )
    return events


def fetch_collabocafe_events():
    html = fetch_url(COLLABOCAFE_URL)
    return parse_collabocafe_html(html)
