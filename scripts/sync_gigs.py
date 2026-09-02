#!/usr/bin/env python3
"""Pull the Upcoming Gigs sheet (published as CSV) into gigs.json.

Sabelle edits a Google Sheet; this turns it into data the site can render.
It is deliberately forgiving about how a date or a time is written, because
the alternative is a show quietly not existing.

A row is only ever dropped for something that makes it meaningless: a date
nothing can parse, or no venue. A time it cannot read is passed through as
typed rather than costing her the whole booking. A sheet that yields no usable
rows at all leaves gigs.json untouched -- a typo should never wipe the list.

gigs.json accumulates. The sheet is authoritative for anything still to come,
but a show whose date has passed is kept even after Sabelle tidies the row out
of the sheet, because the site lists her history under the upcoming dates.

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
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo

    def _today():
        # Every show is in California, so "has it happened yet" is a Pacific
        # question -- and the renderers already answer it that way.
        return datetime.now(ZoneInfo("America/Los_Angeles")).date()
except Exception:  # pragma: no cover - zoneinfo missing/no tzdata
    def _today():
        return date.today()


GIGS_FILE = "gigs.json"
FETCH_TIMEOUT = 30

# Sabelle writes "5-8pm", "5:30 - 8:30 PM", "5pm-8pm", "6 to 9 p.m." -- the
# site shows "5–8PM". The meridiem may sit on either end, or both.
_MER = r"(?:\s*([ap])\.?\s*m?\.?)?"
_CLOCK = r"(\d{1,2}(?::\d{2})?)"
_DASH = r"\s*(?:-{1,2}|–|—|to|until|till|’til)\s*"

TIME_RE = re.compile(f"^\\s*{_CLOCK}{_MER}{_DASH}{_CLOCK}{_MER}\\s*$", re.IGNORECASE)
SINGLE_TIME_RE = re.compile(f"^\\s*{_CLOCK}{_MER}\\s*$", re.IGNORECASE)


def normalize_time(raw):
    """'5:30pm - 8:30pm' -> '5:30–8:30PM'. Returns None if unparseable.

    A range that crosses noon or midnight keeps both meridiems ('11AM–2PM');
    otherwise one on the end says it for both, which is how a gig poster reads.
    """
    m = TIME_RE.match(raw)
    if m:
        start, start_mer, end, end_mer = m.groups()
        start, end = _drop_oclock(start), _drop_oclock(end)
        if not (start_mer or end_mer):
            return None  # "5-8" could be morning or evening; don't guess
        end_mer = (end_mer or start_mer).upper()
        start_mer = (start_mer or end_mer).upper()
        if start_mer != end_mer:
            return f"{start}{start_mer}M–{end}{end_mer}M"
        return f"{start}–{end}{end_mer}M"
    m = SINGLE_TIME_RE.match(raw)
    if m:
        start, mer = m.groups()
        if mer:
            return f"{_drop_oclock(start)}{mer.upper()}M"
    return None


def _drop_oclock(clock):
    """'7:00' -> '7'. The site writes 5-8PM, not 5:00-8:00PM."""
    return clock[:-3] if clock.endswith(":00") else clock


def tidy_time(raw):
    """Whatever she typed, made safe to drop straight onto the poster."""
    return re.sub(r"\s+", " ", raw).strip()[:24]


MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# "Sept 12", "September 12, 2026", "Sep. 12th"
NAME_DAY_RE = re.compile(
    r"^([a-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,)?(?:\s+(\d{4}))?$", re.IGNORECASE
)
# "12 Sept", "12th September 2026"
DAY_NAME_RE = re.compile(
    r"^(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]{3,9})\.?(?:\s*,)?(?:\s+(\d{4}))?$", re.IGNORECASE
)


def _month_from_name(word):
    """'Sept' -> 9. Any unambiguous prefix of at least three letters."""
    word = word.lower()
    for i, name in enumerate(MONTH_NAMES, start=1):
        if name.startswith(word):
            return i
    return None


def _with_year(mo, d, y, today):
    """Pin a month/day to a year, inferring the next occurrence if none given.

    A bare date means the next one coming up: 01/05 typed in December is next
    January, not eleven months ago.
    """
    if y is not None:
        y = int(y)
        return _safe_date(y + 2000 if y < 100 else y, mo, d)
    guess = _safe_date(today.year, mo, d)
    if guess is None:
        return None
    if (today - guess).days > 7:
        return _safe_date(today.year + 1, mo, d)
    return guess


def normalize_date(raw, today):
    """Accept 2026-09-12, 9/12/2026, 9/12/26, a bare 9/12, or 'Sept 12'."""
    raw = raw.strip()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", raw)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        return _safe_date(y, mo, d)

    m = re.match(r"^(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2}|\d{4}))?$", raw)
    if m:
        return _with_year(int(m.group(1)), int(m.group(2)), m.group(3), today)

    for pattern, name_first in ((NAME_DAY_RE, True), (DAY_NAME_RE, False)):
        m = pattern.match(raw)
        if not m:
            continue
        name, day = (m.group(1), m.group(2)) if name_first else (m.group(2), m.group(1))
        mo = _month_from_name(name)
        if mo:
            return _with_year(mo, int(day), m.group(3), today)
    return None


def _safe_date(y, mo, d):
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def smarten(s):
    """Sheets give us "Edgar's"; the site sets it as "Edgar’s"."""
    return re.sub(r"(?<=\w)'(?=\w)", "’", s)


def pick(row, *names):
    """Fetch a column by any of several header spellings."""
    for n in names:
        for k, v in row.items():
            if k and k.strip().lower() == n:
                return (v or "").strip()
    return ""


def load_existing():
    """The gigs.json already in the repo -- where the past-show archive lives."""
    try:
        with open(GIGS_FILE, encoding="utf-8") as f:
            return json.load(f).get("gigs", [])
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as e:
        print(f"WARNING: {GIGS_FILE} is unreadable ({e}); the archive restarts empty.")
        return []


def gig_key(g):
    """Same show, however it was spelled in the sheet that week."""
    return (g.get("date", ""), (g.get("venue") or "").strip().lower())


def is_past(g, today):
    try:
        return date.fromisoformat(g["date"]) < today
    except (KeyError, TypeError, ValueError):
        return False


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

    today = _today()
    gigs, skipped, warnings, data_rows = [], [], [], 0

    for i, row in enumerate(csv.DictReader(io.StringIO(body)), start=2):
        raw_date = pick(row, "date", "day")
        venue = pick(row, "venue", "place")
        city = pick(row, "city", "location", "town")
        raw_time = pick(row, "time", "times", "set time")

        if not any([raw_date, venue, city, raw_time]):
            continue  # blank spacer row
        data_rows += 1

        # Only a missing date or venue makes a row meaningless. A time we
        # cannot read goes through as typed -- losing the whole booking over
        # the time column is a far worse outcome than an odd-looking time.
        problems = []
        parsed = normalize_date(raw_date, today)
        if parsed is None:
            problems.append(f"date {raw_date!r}")
        if not venue:
            problems.append("venue is empty")
        if problems:
            skipped.append(f"  row {i}: {', '.join(problems)}")
            continue

        pretty_time = normalize_time(raw_time) if raw_time else ""
        if raw_time and pretty_time is None:
            pretty_time = tidy_time(raw_time)
            warnings.append(f"  row {i}: kept time {raw_time!r} as typed")

        gigs.append(
            {
                "date": parsed.isoformat(),
                "venue": smarten(venue),
                "city": smarten(city),
                "time": pretty_time or "",
            }
        )

    if data_rows and not gigs:
        print(f"ERROR: all {data_rows} sheet row(s) were unusable. Leaving gigs.json alone.")
        for s in skipped:
            print(s)
        return 1

    # Shows that have already happened stay put whether or not the sheet still
    # lists them; only the future is the sheet's to remove.
    from_sheet = {gig_key(g) for g in gigs}
    archived = [
        g for g in load_existing()
        if is_past(g, today) and gig_key(g) not in from_sheet
    ]
    gigs.extend(archived)

    gigs.sort(key=lambda g: (g["date"], g["venue"]))

    payload = {
        "_comment": (
            "Generated from the Upcoming Gigs Google Sheet by "
            ".github/workflows/sync-gigs.yml. Edit the sheet, not this file. "
            "Shows whose date has passed are kept here as the site's archive "
            "even once they leave the sheet."
        ),
        "gigs": gigs,
    }
    with open(GIGS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    upcoming = sum(1 for g in gigs if not is_past(g, today))
    print(
        f"Wrote {len(gigs)} gig(s) to {GIGS_FILE}: "
        f"{upcoming} upcoming, {len(gigs) - upcoming} past "
        f"({len(archived)} kept from the archive)."
    )
    if warnings:
        print(f"{len(warnings)} time(s) we could not tidy up:")
        for w in warnings:
            print(w)
    if skipped:
        print(f"Skipped {len(skipped)} bad row(s):")
        for s in skipped:
            print(s)
    return 2 if (skipped or warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
