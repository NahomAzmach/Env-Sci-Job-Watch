"""Job Notifier: scrape all sources, diff against known jobs, email new ones.

Usage:
    python scraper/main.py            # scrape, update data/jobs.json, email new jobs
    python scraper/main.py --no-email # scrape and update data only
    python scraper/main.py --test-email  # send a test email and exit
"""
import json
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sources import conservation_job_board, governmentjobs_wa, tamu_job_board
import emailer

ROOT = Path(__file__).resolve().parent.parent
# lives under docs/ so GitHub Pages serves it alongside the dashboard
DATA_FILE = ROOT / "docs" / "data" / "jobs.json"
PRUNE_AFTER_DAYS = 30

SOURCES = [
    ("Conservation Job Board", conservation_job_board.fetch),
    ("TAMU Job Board", tamu_job_board.fetch),
    ("WA State Gov Jobs", governmentjobs_wa.fetch),
]


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"updated": None, "jobs": {}}


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8"
    )


def run(send_email=True):
    now = datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = load_data()
    known = data["jobs"]

    scraped = {}
    errors = []
    for name, fetch in SOURCES:
        try:
            results = fetch()
            print(f"{name}: {len(results)} jobs")
            for j in results:
                scraped[j["id"]] = j
        except Exception:
            errors.append(name)
            print(f"{name}: FAILED\n{traceback.format_exc()}")

    new_jobs = []
    for jid, job in scraped.items():
        if jid in known:
            prev = known[jid]
            job["first_seen"] = prev.get("first_seen", now_iso)
        else:
            job["first_seen"] = now_iso
            new_jobs.append(job)
        job["last_seen"] = now_iso
        known[jid] = job

    # prune jobs that disappeared from the sites long ago
    cutoff = now - timedelta(days=PRUNE_AFTER_DAYS)
    for jid in list(known):
        last = known[jid].get("last_seen") or now_iso
        if datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) < cutoff:
            del known[jid]

    data["updated"] = now_iso
    save_data(data)
    print(f"Total tracked: {len(known)} | New this run: {len(new_jobs)} | Failed sources: {errors or 'none'}")

    if send_email and new_jobs:
        emailer.send_digest(new_jobs, errors)
        print(f"Emailed digest of {len(new_jobs)} new jobs.")
    elif send_email and errors:
        print("No new jobs; skipping email despite source errors.")

    return 0


if __name__ == "__main__":
    if "--test-email" in sys.argv:
        emailer.send_test()
        print("Test email sent.")
        sys.exit(0)
    sys.exit(run(send_email="--no-email" not in sys.argv))
