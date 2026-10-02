#!/usr/bin/env python3
"""
Ticket Triage Automation
========================
Reads a CSV of support tickets, auto-categorizes each ticket by keyword,
assigns a priority (P1-P4), computes the SLA deadline for that priority,
and flags tickets that are breached or at risk.

Usage:
    python triage.py sample_tickets.csv
    python triage.py sample_tickets.csv --report triage_report.csv

Input CSV columns: id, subject, description, impact, created_at (YYYY-MM-DD HH:MM)
"""

import argparse
import csv
import sys
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

CATEGORIES = {
    "network":  ["vpn", "wi-fi", "wifi", "internet", "network", "dns",
                 "latency", "connection", "dropped"],
    "account":  ["password", "login", "log in", "locked", "mfa",
                 "account", "access", "sso", "authentication"],
    "hardware": ["laptop", "printer", "monitor", "keyboard", "mouse",
                 "battery", "hardware", "screen", "charger"],
    "software": ["outlook", "email", "excel", "teams", "software", "install",
                 "update", "crash", "error", "application"],
    "security": ["phishing", "malware", "virus", "breach", "suspicious",
                 "ransomware", "compromised"],
}

# SLA: max hours allowed per priority before breach
SLA_HOURS = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}

# ----------------------------------------------------------------------------
# Triage logic
# ----------------------------------------------------------------------------

def categorize(subject: str, description: str) -> str:
    """Pick the category with the most keyword hits."""
    text = f"{subject} {description}".lower()
    scores = {cat: sum(1 for kw in kws if kw in text)
              for cat, kws in CATEGORIES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


def assign_priority(subject: str, description: str, impact: str) -> str:
    """P1 = critical outage/security, P2 = high impact, P3 = medium, P4 = low."""
    text = f"{subject} {description}".lower()
    critical = ["outage", "system down", "breach", "ransomware",
                "all users", "production down", "data loss"]
    high = ["phishing", "malware", "locked out", "cannot work",
            "payroll", "security"]
    if any(k in text for k in critical):
        return "P1"
    if impact.strip().lower() == "high" or any(k in text for k in high):
        return "P2"
    if impact.strip().lower() == "medium":
        return "P3"
    return "P4"


def sla_status(priority: str, created_at: datetime,
               now: datetime) -> tuple[str, datetime]:
    """Return (status, deadline). Status: ON TRACK / AT RISK / BREACHED."""
    deadline = created_at + timedelta(hours=SLA_HOURS[priority])
    remaining = (deadline - now).total_seconds()
    total = SLA_HOURS[priority] * 3600
    if remaining <= 0:
        return "BREACHED", deadline
    if remaining < total * 0.25:
        return "AT RISK", deadline
    return "ON TRACK", deadline


def triage_row(row: dict, now: datetime) -> dict:
    category = categorize(row["subject"], row["description"])
    priority = assign_priority(row["subject"], row["description"], row["impact"])
    created = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M")
    status, deadline = sla_status(priority, created, now)
    return {
        "id": row["id"],
        "category": category,
        "priority": priority,
        "sla_deadline": deadline.strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "subject": row["subject"],
    }


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-triage support tickets.")
    parser.add_argument("input_csv", help="Tickets CSV file")
    parser.add_argument("--report", default="triage_report.csv",
                        help="Output report CSV (default: triage_report.csv)")
    parser.add_argument("--now", default=None,
                        help="Override 'now' as YYYY-MM-DD HH:MM (for demos)")
    args = parser.parse_args()

    now = (datetime.strptime(args.now, "%Y-%m-%d %H:%M") if args.now
           else datetime.now())

    with open(args.input_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"id", "subject", "description", "impact", "created_at"}
    if not required.issubset(rows[0].keys()):
        print(f"ERROR: input CSV must have columns: {sorted(required)}",
              file=sys.stderr)
        return 1

    results = [triage_row(r, now) for r in rows]

    with open(args.report, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "category", "priority",
                                               "sla_deadline", "status",
                                               "subject"])
        writer.writeheader()
        writer.writerows(results)

    # Console summary, sorted so the most urgent tickets come first
    order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    results.sort(key=lambda r: (order[r["priority"]], r["sla_deadline"]))
    breached = sum(1 for r in results if r["status"] == "BREACHED")
    at_risk = sum(1 for r in results if r["status"] == "AT RISK")

    print(f"\nTriaged {len(results)} tickets -> {args.report}")
    print(f"BREACHED: {breached} | AT RISK: {at_risk} | "
          f"ON TRACK: {len(results) - breached - at_risk}\n")
    print(f"{'ID':<6}{'PRI':<5}{'STATUS':<10}{'CATEGORY':<10}SUBJECT")
    print("-" * 70)
    for r in results:
        print(f"{r['id']:<6}{r['priority']:<5}{r['status']:<10}"
              f"{r['category']:<10}{r['subject'][:38]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
