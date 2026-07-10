#!/usr/bin/env python3
"""Build the shareable gig poster from gigs.json.

Emits two self-contained HTML cards (Instagram post 1080x1350 and story
1080x1920) plus the /gigs landing page. A separate step screenshots the cards
into PNGs, so the graphic is regenerated from the same data the site renders --
the poster can never disagree with the website.
"""

import html
import json
import os
import sys
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo

    TODAY = datetime.now(ZoneInfo("America/Los_Angeles")).date()
except Exception:  # pragma: no cover
    TODAY = date.today()

GIGS_FILE = "gigs.json"
OUT_DIR = "gigs"
INSTAGRAM = "https://www.instagram.com/sabellesings/"
SITE = "sabellesings.com"

MONTHS = [
    "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
    "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
]

FONTS = (
    "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Kalam:wght@300;400;700"
    "&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap"
)


def esc(s):
    return html.escape(s or "", quote=False)


def month_label(gigs):
    """'JULY 2026', or 'JULY–AUGUST 2026' when the run spans months."""
    if not gigs:
        return str(TODAY.year)
    ds = [date.fromisoformat(g["date"]) for g in gigs]
    first, last = ds[0], ds[-1]
    if (first.month, first.year) == (last.month, last.year):
        return f"{MONTHS[first.month - 1]} {first.year}"
    if first.year == last.year:
        return f"{MONTHS[first.month - 1]}–{MONTHS[last.month - 1]} {first.year}"
    return f"{MONTHS[first.month - 1]} {first.year}–{MONTHS[last.month - 1]} {last.year}"


def rows_html(gigs):
    out = []
    for g in gigs:
        d = date.fromisoformat(g["date"])
        day = f'{MONTHS[d.month - 1][:3]} {d.day}'
        time = esc(g.get("time", ""))
        city = esc(g.get("city", ""))
        out.append(
            '<li class="gig">'
            f'<span class="g-date">{esc(day)}</span>'
            '<span class="g-mid">'
            f'<span class="g-venue">{esc(g["venue"])}</span>'
            f'<span class="g-city">{city}</span>'
            "</span>"
            f'<span class="g-time">{time}</span>'
            "</li>"
        )
    return "\n        ".join(out)


CARD_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --golden-hour:#D4A574; --sunset-orange:#E89F71; --dusty-rose:#C08B7C;
  --warm-cream:#FAF3E8; --deep-amber:#B67E5C; --vintage-brown:#6B4E3D;
  --soft-peach:#FFE4D6; --retro-green:#7D8B5F;
}
html,body{ background:#fff; }
body{ display:flex; align-items:center; justify-content:center; }
.card{
  position:relative; overflow:hidden;
  background:
    radial-gradient(circle at 18% 12%, rgba(255,228,214,.85), transparent 42%),
    radial-gradient(circle at 84% 8%,  rgba(232,159,113,.30), transparent 38%),
    radial-gradient(circle at 50% 108%, rgba(212,165,116,.45), transparent 55%),
    var(--warm-cream);
  display:flex; flex-direction:column;
}
/* sun rays behind the header */
.card::before{
  content:""; position:absolute; top:-38%; left:50%; width:150%; aspect-ratio:1;
  transform:translateX(-50%);
  background:repeating-conic-gradient(from 0deg at 50% 50%,
    rgba(232,159,113,.16) 0deg 7deg, transparent 7deg 14deg);
  opacity:.7; pointer-events:none;
}
/* paper grain */
.card::after{
  content:""; position:absolute; inset:0; pointer-events:none; opacity:.05;
  background-image:radial-gradient(#6B4E3D 1px, transparent 1px);
  background-size:5px 5px;
}
.inner{
  position:relative; z-index:2; flex:1; display:flex; flex-direction:column;
  margin:var(--frame); border:3px solid var(--vintage-brown); border-radius:26px;
  padding:var(--pad);
}
.inner::before{
  content:""; position:absolute; inset:14px; border:2px dashed var(--deep-amber);
  border-radius:16px; opacity:.55; pointer-events:none;
}
.head{ text-align:center; }
.name{
  font-family:'Bebas Neue',sans-serif; letter-spacing:.06em; line-height:.92;
  font-size:var(--name-size); color:var(--sunset-orange);
  text-shadow:5px 5px 0 var(--deep-amber), 10px 10px 0 rgba(107,78,61,.18);
}
.tag{
  font-family:'Kalam',cursive; color:var(--dusty-rose);
  font-size:var(--tag-size); margin-top:.35em;
}
.rule{
  display:flex; align-items:center; gap:18px; margin:var(--rule-gap) 0;
  color:var(--golden-hour);
}
.rule span{ flex:1; height:2px; background:currentColor; opacity:.5; }
.rule b{ font-size:calc(var(--tag-size) * .9); }
.title{
  font-family:'Bebas Neue',sans-serif; text-align:center; color:var(--vintage-brown);
  font-size:var(--title-size); letter-spacing:.08em; line-height:1;
}
.month{
  font-family:'Space Mono',monospace; text-align:center; color:var(--deep-amber);
  font-size:var(--month-size); letter-spacing:.3em; margin-top:.5em; font-weight:700;
}
/* One shared set of columns so every row's venue starts at the same x. */
.gigs{
  list-style:none; margin-top:var(--list-top); flex:1;
  display:grid; grid-template-columns:max-content 1fr max-content;
  align-content:center; row-gap:var(--row-gap);
}
.gig{
  grid-column:1 / -1; display:grid; grid-template-columns:subgrid;
  gap:var(--col-gap); align-items:center;
  padding:var(--row-pad) calc(var(--row-pad) * .9);
  border-radius:14px; background:rgba(212,165,116,.13);
}
.gig:nth-child(even){ background:rgba(125,139,95,.10); }
.g-date{
  font-family:'Bebas Neue',sans-serif; color:var(--deep-amber);
  font-size:var(--date-size); letter-spacing:.05em; white-space:nowrap;
}
.g-mid{ display:flex; flex-direction:column; min-width:0; }
.g-venue{
  font-family:'Space Mono',monospace; font-weight:700; color:var(--vintage-brown);
  font-size:var(--venue-size); line-height:1.25;
}
.g-city{
  font-family:'Space Mono',monospace; color:var(--dusty-rose);
  font-size:var(--city-size); margin-top:.15em;
}
.g-time{
  font-family:'Space Mono',monospace; font-weight:700; color:var(--retro-green);
  font-size:var(--time-size); white-space:nowrap; text-align:right;
}
.more{
  grid-column:1 / -1; text-align:center; padding-top:.35em;
  font-family:'Space Mono',monospace; font-style:italic;
  color:var(--deep-amber); font-size:var(--city-size); letter-spacing:.05em;
}
.empty{
  flex:1; display:flex; flex-direction:column; align-items:center;
  justify-content:center; text-align:center; gap:.6em;
  font-family:'Space Mono',monospace; color:var(--vintage-brown);
  font-size:var(--venue-size);
}
.foot{
  margin-top:var(--foot-top); text-align:center;
  font-family:'Space Mono',monospace; color:var(--vintage-brown);
}
.handle{ font-size:var(--handle-size); font-weight:700; color:var(--deep-amber); letter-spacing:.12em; }
.site{ font-size:var(--site-size); color:var(--dusty-rose); margin-top:.45em; letter-spacing:.22em; }
.petals{ position:absolute; z-index:3; color:var(--golden-hour); opacity:.5; }
.p1{ top:3.2%; left:5%;  font-size:var(--petal); transform:rotate(-12deg); }
.p2{ bottom:3.2%; right:5.5%; font-size:var(--petal); transform:rotate(14deg); }
"""

POST_VARS = """
.card{ width:1080px; height:1350px;
  --frame:30px; --pad:46px; --name-size:118px; --tag-size:31px; --rule-gap:18px;
  --title-size:62px; --month-size:22px; --list-top:24px; --col-gap:24px;
  --row-pad:17px; --row-gap:12px; --date-size:42px; --venue-size:25px;
  --city-size:19px; --time-size:23px; --foot-top:22px; --handle-size:28px;
  --site-size:18px; --petal:46px; }
"""

STORY_VARS = """
.card{ width:1080px; height:1920px;
  --frame:32px; --pad:46px; --name-size:150px; --tag-size:38px; --rule-gap:30px;
  --title-size:78px; --month-size:26px; --list-top:40px; --col-gap:22px;
  --row-pad:24px; --row-gap:18px; --date-size:50px; --venue-size:25px;
  --city-size:22px; --time-size:25px; --foot-top:36px; --handle-size:33px;
  --site-size:20px; --petal:60px; }
"""


# Row metrics that must shrink together when the list runs long.
ROW_VARS = {
    #                 post, story
    "date-size": (42, 50),
    "venue-size": (25, 25),
    "city-size": (19, 22),
    "time-size": (23, 25),
    "row-pad": (17, 24),
    "row-gap": (12, 18),
}

# Past this many rows a poster is unreadable, and shrinking text further stops
# helping. Show the first N and point at the site for the rest.
MAX_ROWS = {False: 8, True: 12}  # keyed by is_story

# Rows start shrinking past this count, before the hard cap kicks in.
SHRINK_ABOVE = {False: 6, True: 9}


def scale_for_count(n, story):
    """Shrink rows when the list is long so the card never overflows."""
    limit = SHRINK_ABOVE[story]
    if n <= limit:
        return ""
    k = max(0.7, limit / n)
    idx = 1 if story else 0
    decls = " ".join(
        f"--{name}:{base[idx] * k:.1f}px;" for name, base in ROW_VARS.items()
    )
    return f".card{{ {decls} }}"


def card_html(gigs, story=False):
    cap = MAX_ROWS[story]
    shown, hidden = gigs[:cap], max(0, len(gigs) - cap)
    if shown:
        more = (
            f'\n        <li class="more">+{hidden} more '
            f'{"date" if hidden == 1 else "dates"} at {SITE}</li>'
            if hidden
            else ""
        )
        body = f'<ul class="gigs">\n        {rows_html(shown)}{more}\n      </ul>'
    else:
        body = (
            '<div class="empty"><b>Performing throughout California</b>'
            "<span>DM for bookings &amp; upcoming dates</span></div>"
        )
    vars_css = STORY_VARS if story else POST_VARS
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Sabelle — Upcoming Gigs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>{CARD_CSS}{vars_css}{scale_for_count(len(gigs), story)}</style>
</head><body>
  <div class="card">
    <div class="petals p1">✿</div>
    <div class="petals p2">☼</div>
    <div class="inner">
      <div class="head">
        <div class="name">SABELLE</div>
        <div class="tag">where sunset meets soul</div>
      </div>
      <div class="rule"><span></span><b>✷</b><span></span></div>
      <div class="title">UPCOMING GIGS</div>
      <div class="month">{esc(month_label(gigs))}</div>
      {body}
      <div class="foot">
        <div class="handle">@sabellesings</div>
        <div class="site">{SITE}</div>
      </div>
    </div>
  </div>
</body></html>
"""


def short_day(gig):
    d = date.fromisoformat(gig["date"])
    return f"{MONTHS[d.month - 1][:3]} {d.day}"


def plain_line(gig):
    """One gig as plain text, for the copyable caption."""
    line = f"{short_day(gig)} — {gig['venue']}"
    if gig.get("city"):
        line += f", {gig['city']}"
    if gig.get("time"):
        line += f" · {gig['time']}"
    return line


def landing_html(gigs):
    if gigs:
        items = "\n".join(
            f"      <li><b>{esc(short_day(g))}</b> — {esc(plain_line(g).split(' — ', 1)[1])}</li>"
            for g in gigs
        )
    else:
        items = "      <li>No upcoming dates listed yet.</li>"

    caption = "\n".join(plain_line(g) for g in gigs)
    stamp = TODAY.isoformat()

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Sabelle — Gig Graphics</title>
<link rel="icon" href="../favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="{FONTS}" rel="stylesheet">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#FAF3E8;color:#6B4E3D;font-family:'Space Mono',monospace;
       padding:40px 20px;line-height:1.6}}
  .wrap{{max-width:900px;margin:0 auto}}
  h1{{font-family:'Bebas Neue',sans-serif;font-size:56px;color:#B67E5C;letter-spacing:.05em}}
  .sub{{font-family:'Kalam',cursive;color:#C08B7C;font-size:20px;margin-bottom:28px}}
  .cards{{display:flex;gap:28px;flex-wrap:wrap;margin:28px 0}}
  .col{{flex:1;min-width:260px}}
  .col h2{{font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:.08em;margin-bottom:10px}}
  img{{width:100%;border:3px solid #6B4E3D;border-radius:14px;display:block}}
  a.btn{{display:inline-block;margin-top:12px;background:#E89F71;color:#fff;
        text-decoration:none;padding:12px 22px;border-radius:30px;font-weight:700}}
  a.btn:hover{{background:#B67E5C}}
  ul{{list-style:none;margin:14px 0}}
  li{{padding:10px 14px;background:rgba(212,165,116,.14);border-radius:10px;margin-bottom:8px}}
  .box{{background:rgba(125,139,95,.10);border:2px dashed #7D8B5F;border-radius:14px;
       padding:18px;margin-top:14px}}
  textarea{{width:100%;min-height:130px;border:none;background:transparent;
           font:inherit;color:inherit;resize:vertical}}
  .note{{font-size:13px;color:#C08B7C;margin-top:30px}}
</style></head>
<body><div class="wrap">
  <h1>GIG GRAPHICS</h1>
  <div class="sub">Auto-updated whenever the schedule changes · last built {stamp}</div>

  <div class="cards">
    <div class="col">
      <h2>Instagram Post — 1080×1350</h2>
      <img src="gig-card.png" alt="Sabelle upcoming gigs poster">
      <a class="btn" href="gig-card.png" download>Download post</a>
    </div>
    <div class="col">
      <h2>Story — 1080×1920</h2>
      <img src="gig-card-story.png" alt="Sabelle upcoming gigs story graphic">
      <a class="btn" href="gig-card-story.png" download>Download story</a>
    </div>
  </div>

  <h2 style="font-family:'Bebas Neue',sans-serif;font-size:30px;letter-spacing:.06em">The dates</h2>
  <ul>
{items}
  </ul>

  <div class="box">
    <b>Caption — tap and copy</b>
    <textarea readonly>{caption}

@sabellesings · {SITE}</textarea>
  </div>

  <p class="note">Edit the Google Sheet to change these. The website, both graphics,
  and this page rebuild themselves within a few hours.</p>
</div></body></html>
"""


def main():
    with open(GIGS_FILE, encoding="utf-8") as f:
        data = json.load(f)

    gigs = []
    for g in data.get("gigs", []):
        try:
            if date.fromisoformat(g["date"]) >= TODAY:
                gigs.append(g)
        except (KeyError, ValueError):
            pass
    gigs.sort(key=lambda g: (g["date"], g.get("venue", "")))

    os.makedirs(OUT_DIR, exist_ok=True)
    for name, story in (("card-post.html", False), ("card-story.html", True)):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(card_html(gigs, story=story))
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(landing_html(gigs))

    print(f"Built gig cards for {len(gigs)} upcoming gig(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
