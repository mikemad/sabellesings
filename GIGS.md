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

- **Dates** can be `2026-07-24`, `7/24/2026`, `7/24`, `July 24`, `Jul 24`, or
  `24 July`. A bare `7/24` or `July 24` means the next one coming up, so you can
  type it without thinking about the year.
- **Times** can be `5-8pm`, `5:30 - 8:30 PM`, `5pm-8pm`, `5 to 8 pm`, or
  `11am-2pm`. They all come out looking the same on the site. If a time is
  written some other way it goes on the site exactly as typed — an odd-looking
  time never costs you the booking.
- **Past shows move themselves.** The day after a show, it drops out of
  Upcoming Gigs and reappears under **Past Shows** further down the page, so
  the history builds up on its own. Leave the row in the sheet or delete it —
  once a show has happened the site keeps it either way.
- **Blank rows are ignored**, so you can leave gaps for spacing.
- Changes appear **within a minute or two** if the sheet's **Gigs → Publish
  now** menu is set up (see below); otherwise within about **6 hours**.

A row is only ever dropped for something that makes it meaningless: a date
nothing can read, or a blank venue. Everything else publishes. If the whole
sheet is unreadable, the site just keeps showing the dates it already had — a
bad edit can't take the schedule down.

## Past shows

Everything that has already happened is listed under **Past Shows**, below the
upcoming dates — the point being that a run of steady gigs looks like a run of
steady gigs. The list is grouped by year, newest first, and shows the twelve
most recent with a button for the rest.

The section deliberately carries no total. It can only ever hold shows that
passed through the sheet, which is a fraction of what Sabelle has actually
played, so a count would read as a career tally and undersell her.

Two things to know:

- **The archive keeps growing.** Deleting a past row from the sheet no longer
  removes it from the site. Once a date passes, that show is kept in `gigs.json`
  whether or not the sheet still lists it.
- **To remove a past show for real**, delete it from `gigs.json` (a code change).
  Deleting an *upcoming* show still works exactly as before: take the row out of
  the sheet and it's gone at the next sync.

## The graphics

Every sync rebuilds two posters from the same dates the website uses, so the
graphic can never disagree with the site. Only upcoming shows go on the poster —
the past-show list lives on the website, not on Instagram.

- `gigs/gig-card.png` — 1080×1350, the Instagram feed post
- `gigs/gig-card-story.png` — 1080×1920, the story

Both are on **https://sabellesings.com/gigs/**, along with download buttons and
a plain-text caption to copy. That page is `noindex`, so it won't show up in
search results — it's just for her.

When there are more than 8 shows, the post shows the first 8 and adds
"+N more dates at sabellesings.com" rather than shrinking the text to nothing.
The `/gigs/` page always lists every date.

### The colours change every month

The poster is tinted by the month of the first show on it, cycling through
twelve pastels — periwinkle in January, blush in February, mint in March, and
so on round to frost in December. July keeps the original sunset palette; every
other month is that same recipe rotated to a new hue, so they all sit at the
same weight and none of them comes out looking washed out. Nothing to set: post
a March run and it comes out mint.

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

## Publishing straight away (one time)

Without this, an edit waits for the next six-hourly run. With it, the sheet
tells GitHub the moment it changes and the site updates in a minute or two.

1. **Make a token.** GitHub → **Settings → Developer settings → Personal access
   tokens → Fine-grained tokens → Generate new token**. Scope it to this
   repository only, and give it **Contents: read-only** and **Actions: read and
   write**. Copy the token — GitHub shows it once.
2. **Put it in the sheet's script.** In the spreadsheet: **Extensions → Apps
   Script**. Paste in the contents of `scripts/sheet-trigger.gs` and save. Then
   **Project Settings → Script Properties → Add script property**: name
   `GITHUB_TOKEN`, value the token from step 1.
3. **Add the trigger.** In Apps Script: **Triggers → Add Trigger** →
   function `onSheetChange`, source **From spreadsheet**, type **On change**.
   Save, and approve the permissions prompt.
4. **Check it.** Reload the spreadsheet — a **Gigs** menu appears. **Gigs →
   Publish now** should toast "Publishing…", and the Sync Gigs workflow should
   start in the repo's Actions tab.

A burst of edits collapses into one build: the trigger waits 90 seconds between
pokes, and GitHub cancels a run that a newer one supersedes. If the token is
missing, expires, or GitHub is unreachable, the script gives up quietly — the
six-hourly sync is still there and still catches everything.

> GitHub switches scheduled workflows off in a repository that has had no
> pushes for 60 days. If the dates ever go stale for no obvious reason, push
> anything (or hit **Run workflow**) to wake the schedule back up.

## How it fits together

```
Google Sheet ──sync_gigs.py──> gigs.json ──┬── render_gigs.py ──────> index.html
                                           └── render_gig_card.py ──> gigs/*.html
                                                                        │
                                             shoot_cards.py (Chrome) ───┴──> gigs/*.png
                                             check_cards.py verifies nothing is clipped
```

`.github/workflows/sync-gigs.yml` runs that chain every 6 hours, on demand, and
on a `repository_dispatch` from the sheet's Apps Script. It commits only when
something actually changed, then triggers the Pages deploy. The scheduled run
with no sheet change is what moves shows into the archive once their date
passes.

`render_gigs.py` writes two blocks into `index.html`: `GIGS:START/END` for the
upcoming dates and `PASTGIGS:START/END` for the Past Shows section. The past
list is written out in full and folded down to twelve rows by
`retro-scripts.js`, so it survives with JavaScript off.

`gigs.json` is generated, and it accumulates — the sheet is authoritative for
upcoming dates, but past shows stay in the file once they land there. Edit the
sheet, not the JSON, except when you genuinely need to delete a show from the
archive.

## Running it locally

```sh
export GIGS_SHEET_CSV_URL='https://docs.google.com/.../pub?output=csv'
python3 scripts/sync_gigs.py          # sheet  -> gigs.json   (optional)
python3 scripts/render_gigs.py        # gigs.json -> index.html
python3 scripts/render_gig_card.py    # gigs.json -> gigs/*.html
python3 scripts/shoot_cards.py "$(command -v google-chrome)"   # -> gigs/*.png
python3 scripts/check_cards.py "$(command -v google-chrome)"   # 0 ok, 2 warn, 1 broken
```
