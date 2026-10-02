# Ticket Triage Automation

A Python tool that does the first pass of help-desk triage automatically:
it reads support tickets from a CSV, categorizes each one by keyword,
assigns a priority (P1–P4), computes the SLA deadline for that priority,
and flags tickets that are **BREACHED** or **AT RISK**.

## Why this exists

In a busy support queue, the most expensive mistake is a critical ticket
sitting unread. This script makes sure P1 outages and security incidents
surface to the top instantly, with their SLA countdown attached.

## How it works

1. **Categorize** — keyword matching sorts each ticket into network, account,
   hardware, software, security, or general.
2. **Prioritize** — P1 for outages/security incidents, P2 for high-impact,
   P3 for medium, P4 for low.
3. **SLA tracking** — each priority has a response window
   (P1: 4h, P2: 8h, P3: 24h, P4: 72h). Tickets inside 25% of their window
   are flagged AT RISK; past the deadline, BREACHED.

## Run it

```bash
python triage.py sample_tickets.csv
python triage.py sample_tickets.csv --report my_report.csv
# Reproduce the demo with a fixed "now":
python triage.py sample_tickets.csv --now "2026-09-29 13:00"
```

Output: a `triage_report.csv` plus an urgency-sorted console summary.

## Sample output

```
Triaged 20 tickets -> triage_report.csv
BREACHED: 0 | AT RISK: 2 | ON TRACK: 18

ID    PRI  STATUS    CATEGORY  SUBJECT
----------------------------------------------------------------------
T-106 P1   AT RISK   software  Email system down for all users
T-118 P2   AT RISK   account   Suspicious login from unknown location
T-115 P2   ON TRACK  network   Internet slow across office
...
```

## Files

- `triage.py` — the triage engine (standard library only, no dependencies)
- `sample_tickets.csv` — 20 synthetic demo tickets

## Interview notes

See `INTERVIEW-GUIDE.md` in the portfolio root for the 30-second pitch,
likely interview questions, and honest framing for this project.

> All ticket data here is synthetic and created for demonstration.
