"""Scraper for conservationjobboard.com state listing pages (static HTML)."""
from bs4 import BeautifulSoup

from .common import make_job, make_session

BASE = "https://www.conservationjobboard.com"
STATES = {"washington": "WA", "oregon": "OR", "california": "CA"}
MAX_PAGES = 10


def _text(el):
    return el.get_text(" ", strip=True) if el else ""


def _parse_page(html, state):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select("div.listing__job article"):
        link = card.select_one("h2.listing__job__title a[href]")
        if not link:
            continue
        url = link["href"].split("?")[0]
        title = _text(link)
        org = _text(card.select_one("h3"))
        location = _text(card.select_one("h4"))
        salary = job_type = ""
        for p in card.select("p.listing__job__intro"):
            txt = _text(p)
            if txt.lower().startswith("salary"):
                salary = txt.split(":", 1)[-1].strip()
            elif txt.lower().startswith("job type"):
                job_type = txt.split(":", 1)[-1].strip()
        posted = _text(card.select_one(".listing__job__time"))
        jobs.append(make_job(
            "Conservation Job Board", title, org, location, state, url,
            salary=salary, posted=posted, job_type=job_type,
        ))
    next_link = soup.select_one('a[rel="next"]')
    return jobs, bool(next_link)


def fetch():
    session = make_session()
    jobs = {}
    for slug, state in STATES.items():
        for page in range(1, MAX_PAGES + 1):
            url = f"{BASE}/{slug}" if page == 1 else f"{BASE}/{slug}/{page}"
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            page_jobs, has_next = _parse_page(resp.text, state)
            for j in page_jobs:
                jobs[j["id"]] = j
            if not has_next:
                break
    return list(jobs.values())
