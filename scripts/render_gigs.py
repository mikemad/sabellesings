#!/usr/bin/env python3
"""Render gigs.json into index.html.

Two blocks, both written straight into the static HTML so they stay crawlable
and are never blanked by a failed fetch:

  GIGS:START / GIGS:END          the shows still to come
  PASTGIGS:START / PASTGIGS:END  everything that has already happened

A gig moves from the first block to the second the day after it happens
(Pacific time, since every show is in California), which is what keeps the
upcoming section from going stale on its own.

The past list renders in full. retro-scripts.js collapses it to the most
recent PAST_VISIBLE rows and adds the expand button, so with JavaScript off
the whole history is still there.
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
PAST_START = "<!-- PASTGIGS:START -->"
PAST_END = "<!-- PASTGIGS:END -->"
INSTAGRAM = "https://www.instagram.com/sabellesings/"

# How many past shows stay visible before the "show all" button takes over.
PAST_VISIBLE = 12

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


def render_past_rows(past):
    """Newest first, grouped under a year heading.

    Rows past PAST_VISIBLE are tagged so the script can fold them away; a year
    heading is tagged with its first row, since it is only there for those rows.
    """
    out = []
    year = None
    for i, g in enumerate(past):
        d = date.fromisoformat(g["date"])
        overflow = " past-overflow" if i >= PAST_VISIBLE else ""
        if d.year != year:
            year = d.year
            out.append(f'                <h3 class="past-year{overflow}">{year}</h3>')
        day = f"{MONTHS[d.month - 1][:3]} {d.day}"
        out.append(f'                <div class="tour-date{overflow}">')
        out.append(f'                    <span class="date-day">{esc(day)}</span>')
        out.append(f'                    <span class="date-venue">{esc(g["venue"])}</span>')
        out.append(f'                    <span class="date-city">{esc(g.get("city", ""))}</span>')
        out.append(f'                    <span class="date-time">{esc(g.get("time", ""))}</span>')
        out.append("                </div>")
    return "\n".join(out)


def build_past_block(past):
    """The whole Past Shows section, markers included -- or just the markers."""
    if not past:
        return f"    {PAST_START}\n    {PAST_END}"

    # No count anywhere in here. This section only holds what has passed
    # through the sheet, which is a fraction of what she has actually played --
    # a total would read as a career tally and undersell her.
    total = len(past)
    hidden = total - PAST_VISIBLE
    lines = [
        f"    {PAST_START}",
        "    <!-- Past Shows -->",
        '    <section class="tour-section past-section" id="past-shows"'
        ' aria-labelledby="past-shows-title">',
        '        <div class="tour-poster">',
        '            <div class="poster-header">',
        '                <h2 class="poster-title" id="past-shows-title">PAST SHOWS</h2>',
        '                <p class="poster-subtitle">Where she\'s been playing</p>',
        "            </div>",
        '            <div class="tour-dates" id="past-gigs">',
        render_past_rows(past),
        "            </div>",
    ]
    if total > PAST_VISIBLE:
        lines.append(
            '            <button class="past-toggle" type="button" hidden'
            f' aria-expanded="true" aria-controls="past-gigs" data-hidden="{hidden}">'
            f"Show {hidden} more</button>"
        )
    lines += ["        </div>", "    </section>", f"    {PAST_END}"]
    return "\n".join(lines)


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


def replace_block(src, start, end, block):
    """Swap whatever sits between the markers for a freshly built block.

    The markers' own indentation is already in src, so the replacement drops
    the leading whitespace of its first line.
    """
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.DOTALL)
    return pattern.sub(lambda _: block.strip(), src, count=1)


def main():
    with open(GIGS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    upcoming, past = [], []
    for g in data.get("gigs", []):
        try:
            (upcoming if date.fromisoformat(g["date"]) >= TODAY else past).append(g)
        except (KeyError, ValueError):
            print(f"WARNING: skipping malformed gig entry: {g!r}")
    upcoming.sort(key=lambda g: (g["date"], g.get("venue", "")))
    past.sort(key=lambda g: (g["date"], g.get("venue", "")), reverse=True)

    with open(INDEX, encoding="utf-8") as f:
        src = f.read()

    for marker in (START, END, PAST_START, PAST_END):
        if marker not in src:
            print(f"ERROR: {INDEX} is missing the {marker} marker.")
            return 1

    updated = replace_block(src, START, END, build_block(upcoming))
    updated = replace_block(updated, PAST_START, PAST_END, build_past_block(past))

    if updated == src:
        print(f"No change ({len(upcoming)} upcoming, {len(past)} past).")
        return 0

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(updated)
    print(f"Rendered {len(upcoming)} upcoming and {len(past)} past gig(s) into {INDEX}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
