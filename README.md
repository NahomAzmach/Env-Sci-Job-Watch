# Job Notifier 🌲

A free, always-on watcher for conservation / natural-resources jobs. Twice a day it checks:

- **[Conservation Job Board](https://www.conservationjobboard.com)** — Washington, Oregon, California
- **[TAMU Natural Resources Job Board](https://jobs.rwfm.tamu.edu)** — WA, OR, CA
- **[Washington State government jobs](https://www.governmentjobs.com/careers/washington)** — Dept. of Ecology, Fish & Wildlife, Natural Resources, Transportation

New jobs are emailed as a digest, and every tracked job appears on a filterable dashboard.

## How it works

- `scraper/main.py` scrapes all sources, diffs against `docs/data/jobs.json`, emails anything new, and saves the updated data.
- `.github/workflows/check-jobs.yml` runs it on GitHub Actions at ~7 AM and ~5 PM Pacific, then commits the updated data.
- `docs/index.html` is the dashboard, served free by GitHub Pages from the `docs/` folder.

## One-time setup

1. **Push this folder to a GitHub repository** (public repos get free unlimited Actions minutes).
2. **Gmail app password**: Google Account → Security → 2-Step Verification (must be on) → App passwords → create one named "Job Notifier".
3. **Repo secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `GMAIL_ADDRESS` — the Gmail address that sends the digests
   - `GMAIL_APP_PASSWORD` — the app password from step 2
   - `RECIPIENT_EMAIL` — who gets the emails (comma-separated for several people; optional, defaults to the sender)
4. **Dashboard**: Settings → Pages → Source: "Deploy from a branch" → branch `main`, folder `/docs`. Your dashboard will be at `https://<username>.github.io/<repo>/`.
5. Optionally add a repository **variable** `DASHBOARD_URL` with that URL so emails link to it.
6. Test it: Actions tab → "Check for new jobs" → Run workflow.

## Changing who gets the emails

Edit the `RECIPIENT_EMAIL` secret on GitHub. Nothing else to change.

## Local testing

```
pip install -r scraper/requirements.txt
python scraper/main.py --no-email     # scrape only
copy .env.example .env                # then fill it in
python scraper/main.py --test-email   # send a test email
python -m http.server 8765 --directory docs   # dashboard at http://localhost:8765
```
