"""Scraper for governmentjobs.com/careers/washington (NeoGov), filtered to
selected departments via the same XHR HTML partials the site's own JS uses.

Pagination is only stable when sorted by PositionTitle; sorting by PostingDate
reorders results between page requests and silently drops jobs."""
import re

from bs4 import BeautifulSoup

from .common import make_job, make_session

LIST_URL = "https://www.governmentjobs.com/careers/home/index"
JOB_URL_BASE = "https://www.governmentjobs.com"
MAX_PAGES = 60

DEPARTMENTS = [
    "Dept. of Ecology",
    "Dept. of Fish and Wildlife",
    "Dept. of Natural Resources",
    "Dept. of Transportation",
]


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for item in soup.select("li.list-item[data-job-id]"):
        link = item.select_one("a.item-details-link[href]")
        if not link:
            continue
        dept = link.get("data-department-name", "")
        meta = [li.get_text(" ", strip=True) for li in item.select("ul.list-meta > li")]
        location = meta[0] if meta else ""
        salary = job_type = ""
        for m in meta[1:]:
            if m.startswith("Category:") or m.startswith("Department:"):
                continue
            # e.g. "Full Time - Permanent - $4,880.00 - $7,994.00 Monthly"
            if "$" in m:
                parts = m.split("$", 1)
                job_type = parts[0].strip(" -")
                salary = "$" + parts[1].strip()
            else:
                job_type = m
        posted_el = item.select_one(".list-entry-starts")
        deadline_el = item.select_one(".list-entry-ends")
        jobs.append({
            "dept": dept,
            "job": make_job(
                "WA State Gov Jobs",
                link.get_text(" ", strip=True),
                dept,
                location, "WA",
                JOB_URL_BASE + link["href"],
                salary=salary,
                posted=posted_el.get_text(" ", strip=True) if posted_el else "",
                deadline=deadline_el.get_text(" ", strip=True) if deadline_el else "",
                job_type=job_type,
            ),
        })
    total = 0
    counter = soup.select_one("#job-postings-number")
    if counter:
        m = re.search(r"\d+", counter.get_text())
        if m:
            total = int(m.group())
    return jobs, total


def fetch():
    session = make_session()
    session.headers["X-Requested-With"] = "XMLHttpRequest"
    jobs = {}
    for page in range(1, MAX_PAGES + 1):
        resp = session.get(
            LIST_URL,
            params=[
                ("agency", "washington"),
                ("sort", "PositionTitle"),
                ("isDescendingSort", "false"),
                *[("department", d) for d in DEPARTMENTS],
                ("page", page),
            ],
            timeout=30,
        )
        resp.raise_for_status()
        page_jobs, _total = _parse_page(resp.text)
        before = len(jobs)
        for entry in page_jobs:
            j = entry["job"]
            jobs[j["id"]] = j
        if not page_jobs or len(jobs) == before:
            break
    return list(jobs.values())
