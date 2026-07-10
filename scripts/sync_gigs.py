#!/usr/bin/env python3
"""Pull the Upcoming Gigs sheet (published as CSV) into gigs.json.

Sabelle edits a Google Sheet; this turns it into data the site can render.
Bad rows are skipped rather than published, and a sheet that yields no usable
rows at all leaves gigs.json untouched -- a typo should never wipe the list.

Exit codes:
  0  gigs.json is good (possibly unchanged)
  1  nothing was written; the previous gigs.json still stands
  2  gigs.json was written, but some rows were skipped -- look at the log
"""

import csv
import io
import json
import os
import re
import sys
import urllib.request
from datetime import date

GIGS_FILE = "gigs.json"
FETCH_TIMEOUT = 30

# Sabelle types "5-8pm" or "5:30 - 8:30 PM"; the site shows "5–8PM".
TIME_RE = re.compile(
    r"^\s*(\d{1,2}(?::\d{2})?)\s*(?:-|--|–|—|to)\s*(\d{1,2}(?::\d{2})?)\s*([ap])\.?m\.?\s*$",
    re.IGNORECASE,
)
SINGLE_TIME_RE = re.compile(r"^\s*(\d{1,2}(?::\d{2})?)\s*([ap])\.?m\.?\s*$", re.IGNORECASE)


def normalize_time(raw):
    """'5:30 - 8:30 pm' -> '5:30–8:30PM'. Returns None if unparseable."""
    m = TIME_RE.match(raw)
    if m:
        start, end, mer = m.groups()
        return f"{start}–{end}{mer.upper()}M"
    m = SINGLE_TIME_RE.match(raw)
    if m:
        start, mer = m.groups()
        return f"{start}{mer.upper()}M"
    return None


def normalize_date(raw, today):
    """Accept 2026-07-09, 7/9/2026, 7/9/26, or a bare 7/9 (year inferred).

    A bare month/day means the next occurrence: 01/05 typed in December is
    next January, not eleven months ago.
    """
    raw = raw.strip()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", raw)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        return _safe_date(y, mo, d)

    m = re.match(r"^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2}|\d{4}))?$", raw)
    if m:
        mo, d, y = m.group(1), m.group(2), m.group(3)
        mo, d = int(mo), int(d)
        if y is None:
            guess = _safe_date(today.year, mo, d)
            if guess is None:
                return None
            # Bare date already past by more than a week -> they mean next year.
            if (today - guess).days > 7:
                return _safe_date(today.year + 1, mo, d)
            return guess
        y = int(y)
        if y < 100:
            y += 2000
        return _safe_date(y, mo, d)
    return None


def _safe_date(y, mo, d):
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def pick(row, *names):
    """Fetch a column by any of several header spellings."""
    for n in names:
        for k, v in row.items():
            if k and k.strip().lower() == n:
                return (v or "").strip()
    return ""


def main():
    url = os.environ.get("GIGS_SHEET_CSV_URL", "").strip()
    if not url:
        print("GIGS_SHEET_CSV_URL is not set; leaving gigs.json alone.")
        return 1

    try:
        with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT) as resp:
            body = resp.read().decode("utf-8-sig")
    except Exception as e:
        print(f"ERROR: could not fetch the sheet: {e}")
        print("Leaving gigs.json alone.")
        return 1

    if "<html" in body[:200].lower():
        print("ERROR: sheet URL returned HTML, not CSV.")
        print("Use File > Share > Publish to web, and pick 'Comma-separated values'.")
        return 1

    today = date.today()
    gigs, skipped, data_rows = [], [], 0

    for i, row in enumerate(csv.DictReader(io.StringIO(body)), start=2):
        raw_date = pick(row, "date", "day")
        venue = pick(row, "venue", "place")
        city = pick(row, "city", "location", "town")
        raw_time = pick(row, "time", "times", "set time")

        if not any([raw_date, venue, city, raw_time]):
            continue  # blank spacer row
        data_rows += 1

        problems = []
        parsed = normalize_date(raw_date, today)
        if parsed is None:
            problems.append(f"date {raw_date!r}")
        if not venue:
            problems.append("venue is empty")
        pretty_time = normalize_time(raw_time) if raw_time else ""
        if raw_time and pretty_time is None:
            problems.append(f"time {raw_time!r}")

        if problems:
            skipped.append(f"  row {i}: {', '.join(problems)}")
            continue

        gigs.append(
            {
                "date": parsed.isoformat(),
                "venue": venue,
                "city": city,
                "time": pretty_time or "",
            }
        )

    if data_rows and not gigs:
        print(f"ERROR: all {data_rows} sheet row(s) were unusable. Leaving gigs.json alone.")
        for s in skipped:
            print(s)
        return 1

    gigs.sort(key=lambda g: (g["date"], g["venue"]))

    payload = {
        "_comment": (
            "Generated from the Upcoming Gigs Google Sheet by "
            ".github/workflows/sync-gigs.yml. Edit the sheet, not this file."
        ),
        "gigs": gigs,
    }
    with open(GIGS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Wrote {len(gigs)} gig(s) to {GIGS_FILE}.")
    if skipped:
        print(f"Skipped {len(skipped)} bad row(s):")
        for s in skipped:
            print(s)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
