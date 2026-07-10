# Updating the gigs

Sabelle edits one Google Sheet. Within a few hours the website, the Instagram
graphics, and the shareable page at `/gigs/` all update themselves. Nobody
touches code, and nobody has to remember to delete a show after it happens.

## For Sabelle

Open the **Upcoming Gigs** sheet and put one show per row:

| Date | Venue | City | Time |
|------|-------|------|------|
| 2026-07-24 | Edgar's at the Quail Lodge | Carmel, CA | 5:30-8:30pm |
| 2026-07-31 | Carmel Valley Athletic Club | Carmel Valley, CA | 5-7pm |

That's the whole job. A few things worth knowing:

- **Dates** can be `2026-07-24`, `7/24/2026`, or just `7/24`. A bare `7/24` means
  the next one coming up, so you can type it without thinking about the year.
- **Times** can be `5-8pm`, `5:30 - 8:30 PM`, or `5 to 8 pm`. They all come out
  looking the same on the site.
- **Past shows disappear on their own.** Leave them in the sheet or delete them,
  whichever you like — the site only ever shows what hasn't happened yet.
- **Blank rows are ignored**, so you can leave gaps for spacing.
- Changes take up to about **6 hours** to appear. To see them right away, ask
  Mike to run the sync, or use the **Run workflow** button on the Sync Gigs
  action in GitHub.

If you typo something, that one row is skipped and the rest still publish. If
the whole sheet is unreadable, the site just keeps showing the dates it already
had — a bad edit can't take the schedule down.

## The graphics

Every sync rebuilds two posters from the same dates the website uses, so the
graphic can never disagree with the site:

- `gigs/gig-card.png` — 1080×1350, the Instagram feed post
- `gigs/gig-card-story.png` — 1080×1920, the story

Both are on **https://sabellesings.com/gigs/**, along with download buttons and
a plain-text caption to copy. That page is `noindex`, so it won't show up in
search results — it's just for her.

When there are more than 8 shows, the post shows the first 8 and adds
"+N more dates at sabellesings.com" rather than shrinking the text to nothing.
The `/gigs/` page always lists every date.

## Setup (one time)

1. Make a Google Sheet with the header row `Date, Venue, City, Time`. Import
   `gigs-template.csv` to get the format.
2. **File → Share → Publish to web**. Under it, pick the sheet's tab and choose
   **Comma-separated values (.csv)**, not "Web page". Publish, copy the link.
3. In GitHub: **Settings → Secrets and variables → Actions → Variables → New
   repository variable**. Name it `GIGS_SHEET_CSV_URL`, paste the link.
4. Run the **Sync Gigs** workflow once by hand to confirm it works.

Until step 3 is done the workflow is harmless: it logs a warning, leaves
`gigs.json` alone, and still expires past shows.

## How it fits together

```
Google Sheet ──sync_gigs.py──> gigs.json ──┬── render_gigs.py ──────> index.html
                                           └── render_gig_card.py ──> gigs/*.html
                                                                        │
                                             shoot_cards.py (Chrome) ───┴──> gigs/*.png
                                             check_cards.py verifies nothing is clipped
```

`.github/workflows/sync-gigs.yml` runs that chain every 6 hours and on demand,
commits only when something actually changed, and then triggers the Pages
deploy. The scheduled run with no sheet change is what drops shows once their
date passes.

`gigs.json` is generated. Edit the sheet, not the JSON, or the next sync will
overwrite you.

## Running it locally

```sh
export GIGS_SHEET_CSV_URL='https://docs.google.com/.../pub?output=csv'
python3 scripts/sync_gigs.py          # sheet  -> gigs.json   (optional)
python3 scripts/render_gigs.py        # gigs.json -> index.html
python3 scripts/render_gig_card.py    # gigs.json -> gigs/*.html
python3 scripts/shoot_cards.py "$(command -v google-chrome)"   # -> gigs/*.png
python3 scripts/check_cards.py "$(command -v google-chrome)"   # 0 ok, 2 warn, 1 broken
```
