"""Send the new-jobs digest email via Gmail SMTP.

Configuration (env vars, or a .env file in the project root):
    GMAIL_ADDRESS       sender Gmail address
    GMAIL_APP_PASSWORD  Gmail app password (not your normal password)
    RECIPIENT_EMAIL     comma-separated recipients; defaults to GMAIL_ADDRESS
    DASHBOARD_URL       optional link shown at the bottom of the email
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GREEN = "#2d5a3d"
SAND = "#f5f1e8"


def _config():
    sender = os.environ.get("GMAIL_ADDRESS", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not sender or not password:
        raise RuntimeError(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set (env or .env file)."
        )
    recipients = [
        r.strip()
        for r in os.environ.get("RECIPIENT_EMAIL", sender).split(",")
        if r.strip()
    ]
    return sender, password, recipients


def _job_row(job):
    bits = [b for b in [job.get("location"), job.get("job_type"), job.get("salary")] if b]
    meta = " &middot; ".join(bits)
    deadline = job.get("deadline", "")
    deadline_html = (
        f'<div style="color:#8a6d3b;font-size:13px;margin-top:2px;">Deadline: {deadline}</div>'
        if deadline else ""
    )
    return f"""
    <div style="background:#fff;border:1px solid #e3ddd0;border-radius:8px;padding:14px 16px;margin-bottom:10px;">
      <a href="{job['url']}" style="color:{GREEN};font-weight:bold;font-size:16px;text-decoration:none;">{job['title']}</a>
      <div style="color:#555;font-size:14px;margin-top:4px;">{job.get('org','')}</div>
      <div style="color:#777;font-size:13px;margin-top:2px;">{meta}</div>
      {deadline_html}
    </div>"""


def build_html(new_jobs, errors=()):
    by_source = {}
    for j in new_jobs:
        by_source.setdefault(j["source"], []).append(j)

    sections = ""
    for source, jobs in sorted(by_source.items()):
        rows = "".join(_job_row(j) for j in jobs)
        sections += f"""
        <h2 style="color:{GREEN};font-size:18px;border-bottom:2px solid #cdd9c3;padding-bottom:6px;margin:24px 0 12px;">
          {source} <span style="color:#999;font-weight:normal;font-size:14px;">({len(jobs)} new)</span>
        </h2>{rows}"""

    error_html = ""
    if errors:
        error_html = f"""
        <p style="color:#a33;font-size:13px;">Note: could not check {', '.join(errors)} this run.</p>"""

    dashboard = os.environ.get("DASHBOARD_URL", "").strip()
    dash_html = (
        f'<p style="margin-top:24px;"><a href="{dashboard}" style="color:{GREEN};">Open the job dashboard &rarr;</a></p>'
        if dashboard else ""
    )

    return f"""
    <div style="background:{SAND};padding:24px;font-family:Segoe UI,Arial,sans-serif;">
      <div style="max-width:640px;margin:0 auto;">
        <h1 style="color:{GREEN};font-size:22px;">&#127807; {len(new_jobs)} new job{'s' if len(new_jobs) != 1 else ''} found</h1>
        {sections}
        {error_html}
        {dash_html}
        <p style="color:#aaa;font-size:12px;margin-top:24px;">Job Notifier &middot; watching Conservation Job Board, TAMU Natural Resources Job Board, and WA State government jobs</p>
      </div>
    </div>"""


def _send(subject, html, sender, password, recipients):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, password)
        smtp.sendmail(sender, recipients, msg.as_string())


def send_digest(new_jobs, errors=()):
    sender, password, recipients = _config()
    subject = f"\U0001f33f {len(new_jobs)} new conservation job{'s' if len(new_jobs) != 1 else ''}"
    _send(subject, build_html(new_jobs, errors), sender, password, recipients)


def send_test():
    sender, password, recipients = _config()
    sample = [{
        "source": "Conservation Job Board",
        "title": "Test Job — your notifier is working!",
        "org": "Job Notifier setup",
        "location": "Olympia, WA",
        "salary": "$1 per smile",
        "deadline": "",
        "job_type": "Permanent",
        "url": "https://example.com",
    }]
    _send("\U0001f331 Job Notifier test email", build_html(sample), sender, password, recipients)
