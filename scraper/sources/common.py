"""Shared helpers for all job sources."""
import hashlib

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def job_id(source: str, url: str) -> str:
    return hashlib.sha1(f"{source}|{url}".encode()).hexdigest()[:16]


def make_job(source, title, org, location, state, url, *, salary="", deadline="",
             posted="", job_type="") -> dict:
    return {
        "id": job_id(source, url),
        "source": source,
        "title": title.strip(),
        "org": org.strip(),
        "location": location.strip(),
        "state": state,
        "salary": salary.strip(),
        "deadline": deadline.strip(),
        "posted": posted.strip(),
        "job_type": job_type.strip(),
        "url": url,
    }
