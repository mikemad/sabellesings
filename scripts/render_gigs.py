#!/usr/bin/env python3
"""Render gigs.json into the Upcoming Gigs block of index.html.

Rows are written between the GIGS:START / GIGS:END markers, so the shows stay
in the static HTML -- crawlable, and never blanked by a failed fetch.

Gigs are dropped the day after they happen (Pacific time, since every show is
in California), which is what keeps the section from going stale on its own.
"""

import html
import json
import re
import sys
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo

    TODAY = datetime.now(ZoneInfo("America/Los_Angeles")).date()
except Exception:  # pragma: no cover - zoneinfo missing/no tzdata
    TODAY = date.today()

INDEX = "index.html"
GIGS_FILE = "gigs.json"
START = "<!-- GIGS:START -->"
END = "<!-- GIGS:END -->"
INSTAGRAM = "https://www.instagram.com/sabellesings/"

MONTHS = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
]


def esc(s):
    return html.escape(s, quote=False)


def render_rows(gigs):
    out = []
    for g in gigs:
        d = date.fromisoformat(g["date"])
        day = f"{MONTHS[d.month - 1]} {d.day}"
        out.append('                <div class="tour-date">')
        out.append(f'                    <span class="date-day">{esc(day)}</span>')
        out.append(f'                    <span class="date-venue">{esc(g["venue"])}</span>')
        out.append(f'                    <span class="date-city">{esc(g.get("city", ""))}</span>')
        out.append(f'                    <span class="date-time">{esc(g.get("time", ""))}</span>')
        out.append("                </div>")
    return "\n".join(out)


def render_empty():
    return (
        '                <div class="tour-date empty-state">\n'
        f'                    <span class="date-day">{TODAY.year}</span>\n'
        '                    <span class="date-venue">Performing throughout California</span>\n'
        f'                    <span class="date-city">Follow <a href="{INSTAGRAM}" target="_blank"'
        ' rel="noopener">@sabellesings</a> for upcoming dates or DM for bookings</span>\n'
        "                </div>"
    )


def build_block(gigs):
    lines = [f"            {START}", '            <div class="tour-dates" id="upcoming-gigs">']
    if gigs:
        lines.append(render_rows(gigs))
    else:
        lines.append(render_empty())
    lines.append("            </div>")
    if gigs:
        lines.append(
            '            <p class="gigs-note">More dates coming — follow '
            f'<a href="{INSTAGRAM}" target="_blank" rel="noopener">@sabellesings</a>'
            " or DM for bookings</p>"
        )
    lines.append(f"            {END}")
    return "\n".join(lines)


def main():
    with open(GIGS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    upcoming = []
    for g in data.get("gigs", []):
        try:
            if date.fromisoformat(g["date"]) >= TODAY:
                upcoming.append(g)
        except (KeyError, ValueError):
            print(f"WARNING: skipping malformed gig entry: {g!r}")
    upcoming.sort(key=lambda g: (g["date"], g.get("venue", "")))

    with open(INDEX, encoding="utf-8") as f:
        src = f.read()

    if START not in src or END not in src:
        print(f"ERROR: {INDEX} is missing the {START} / {END} markers.")
        return 1

    pattern = re.compile(
        re.escape(START) + ".*?" + re.escape(END), re.DOTALL
    )
    new_block = build_block(upcoming)
    # Re-anchor on the marker's own indentation so we replace the full line.
    updated = pattern.sub(lambda _: new_block.strip(), src, count=1)
    # sub() dropped the leading indent of the START line; it is already in src.

    if updated == src:
        print(f"No change ({len(upcoming)} upcoming gig(s)).")
        return 0

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"Rendered {len(upcoming)} upcoming gig(s) into {INDEX}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
