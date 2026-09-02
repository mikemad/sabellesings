#!/usr/bin/env python3
"""Assert the generated cards actually look right.

Three things silently ruin the poster: a venue name that wraps to a second
line, content taller than the framed panel, and a panel taller than the card so
its border and dashed inset get sliced off at the bottom. That last one is the
sneaky one -- the footer text can still be comfortably inside the card while the
border it sits in has run off the edge. All three are invisible to a plain
screenshot diff, so check them in a real browser.

A clipped card is broken and must block the build. A wrapped venue is merely
ugly -- an unusually long venue name should never stop Sabelle's dates from
going live -- so it warns instead.

Usage: check_cards.py <path-to-chrome-or-headless-shell>
Exit:  0 = clean, 2 = cosmetic warning, 1 = card is broken
"""

import json
import os
import re
import subprocess
import sys
import tempfile

CARDS = [("gigs/card-post.html", 1080, 1350), ("gigs/card-story.html", 1080, 1920)]

PROBE = """<script>
addEventListener('load',()=>{setTimeout(()=>{
  const card=document.querySelector('.card');
  const wrapped=[];
  document.querySelectorAll('.g-venue').forEach(v=>{
    const lh=parseFloat(getComputedStyle(v).lineHeight);
    const lines=Math.round(v.getBoundingClientRect().height/lh);
    if(lines>1) wrapped.push(v.textContent);
  });
  const inner=document.querySelector('.inner');
  const overflow=Math.max(0, Math.ceil(inner.scrollHeight - inner.clientHeight));
  const foot=document.querySelector('.foot').getBoundingClientRect();
  const cardBox=card.getBoundingClientRect();
  // The panel carries the border and the dashed inset. It is margined off the
  // card on every side, so its bottom plus that margin has to stay inside.
  const innerBox=inner.getBoundingClientRect();
  const frame=parseFloat(getComputedStyle(inner).marginBottom)||0;
  const framePast=Math.max(0, Math.ceil(innerBox.bottom + frame - cardBox.bottom));
  // The panel is pinned to the card, so a list that is too tall no longer
  // pushes the border out -- it spills its own rows instead. The list centres
  // its content, so a spill goes off both ends and has to be measured on each.
  const list=document.querySelector('.gigs');
  let rowsPast=0;
  if(list){
    const rows=[...document.querySelectorAll('.gig, .more')];
    const lb=list.getBoundingClientRect();
    if(rows.length){
      rowsPast=Math.ceil(Math.max(0, lb.top-rows[0].getBoundingClientRect().top)
              + Math.max(0, rows[rows.length-1].getBoundingClientRect().bottom-lb.bottom));
    }
  }
  document.title='PROBE '+JSON.stringify({
    wrapped, overflow, framePast, rowsPast,
    footBottom:Math.ceil(foot.bottom), cardBottom:Math.floor(cardBox.bottom)
  });
},1500)});
</script>"""


def probe(chrome, path, w, h):
    src = open(path, encoding="utf-8").read()
    fd, tmp = tempfile.mkstemp(suffix=".html", dir="gigs")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(src.replace("</body>", PROBE + "</body>"))
        dom = subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=20000", f"--window-size={w},{h}",
                "--dump-dom", f"file://{os.path.abspath(tmp)}",
            ],
            capture_output=True, text=True, timeout=120,
        ).stdout
    finally:
        os.unlink(tmp)

    m = re.search(r"PROBE (\{.*?\})</title>", dom, re.DOTALL)
    if not m:
        raise SystemExit(f"FAIL {path}: probe did not run (fonts or browser issue)")
    return json.loads(m.group(1))


def main():
    chrome = sys.argv[1] if len(sys.argv) > 1 else "chrome"
    broken, warnings = [], []
    for path, w, h in CARDS:
        r = probe(chrome, path, w, h)
        name = os.path.basename(path)

        if r["overflow"] > 0:
            broken.append(f"{name}: content overflows the card by {r['overflow']}px")
        if r["framePast"] > 0:
            broken.append(
                f"{name}: the framed panel runs {r['framePast']}px past the card, "
                "so its border is clipped"
            )
        if r["rowsPast"] > 0:
            broken.append(
                f"{name}: the dates spill {r['rowsPast']}px out of the list area"
            )
        if r["footBottom"] > r["cardBottom"]:
            broken.append(
                f"{name}: footer is clipped "
                f"({r['footBottom']}px > card bottom {r['cardBottom']}px)"
            )
        if r["wrapped"]:
            warnings.append(f"{name}: venue name wraps to 2 lines: {r['wrapped']}")

        bad = r["overflow"] > 0 or r["framePast"] > 0 or r["rowsPast"] > 0
        status = "BROKEN" if bad else ("warn" if r["wrapped"] else "ok")
        print(
            f"{status}: {name} overflow={r['overflow']}px "
            f"framePast={r['framePast']}px rowsPast={r['rowsPast']}px "
            f"wrapped={len(r['wrapped'])}"
        )

    if broken:
        print("\nBroken:")
        print("\n".join("  - " + f for f in broken))
        return 1
    if warnings:
        print("\nWarnings (not fatal):")
        print("\n".join("  - " + f for f in warnings))
        return 2
    print("\nCards look good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
