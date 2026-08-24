"""Scraper for jobs.rwfm.tamu.edu (Texas A&M Natural Resources Job Board)."""
import re

from bs4 import BeautifulSoup

from .common import make_job, make_session

BASE = "https://jobs.rwfm.tamu.edu"
STATES = ["WA", "OR", "CA"]
PAGE_SIZE = 100
MAX_PAGES = 10


def _fields(card):
    """Parse the label/value grid inside a result card into a dict."""
    out = {}
    cols = [d.get_text(" ", strip=True) for d in card.select(".container-fluid div[class*='col-']")]
    for label, value in zip(cols, cols[1:]):
        if label.endswith(":"):
            out[label.rstrip(":").strip()] = value
    return out


def _parse_page(html, state):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.select('a.list-group-item[id$="-result"]'):
        m = re.match(r"job-(\d+)-result", card.get("id", ""))
        if not m:
            continue
        url = f"{BASE}/view-job/?id={m.group(1)}"
        title = card.select_one("h6")
        org = card.select_one("p")
        f = _fields(card)
        jobs.append(make_job(
            "TAMU Job Board",
            title.get_text(" ", strip=True) if title else "(untitled)",
            org.get_text(" ", strip=True) if org else "",
            f.get("Location", ""), state, url,
            salary=f.get("Salary", ""),
            deadline=f.get("Application Deadline", ""),
            posted=f.get("Published", ""),
        ))
    total = 0
    h3 = soup.find(string=re.compile(r"Results:\s*\("))
    if h3:
        m = re.search(r"of\s+(\d+)\)", h3)
        if m:
            total = int(m.group(1))
    return jobs, total


def fetch():
    session = make_session()
    jobs = {}
    for state in STATES:
        for page in range(1, MAX_PAGES + 1):
            resp = session.get(
                f"{BASE}/search/",
                params={"location-state": state, "PageSize": PAGE_SIZE, "PageNum": page},
                timeout=30,
            )
            resp.raise_for_status()
            page_jobs, total = _parse_page(resp.text, state)
            for j in page_jobs:
                jobs[j["id"]] = j
            if not page_jobs or page * PAGE_SIZE >= total:
                break
    return list(jobs.values())
