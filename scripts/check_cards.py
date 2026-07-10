#!/usr/bin/env python3
"""Assert the generated cards actually look right.

Two things silently ruin the poster: a venue name that wraps to a second line,
and content that overflows the fixed 1080x1350 / 1080x1920 canvas so the footer
gets clipped. Both are invisible to a plain screenshot diff, so check them in a
real browser.

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
  document.title='PROBE '+JSON.stringify({
    wrapped, overflow,
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
        if r["footBottom"] > r["cardBottom"]:
            broken.append(
                f"{name}: footer is clipped "
                f"({r['footBottom']}px > card bottom {r['cardBottom']}px)"
            )
        if r["wrapped"]:
            warnings.append(f"{name}: venue name wraps to 2 lines: {r['wrapped']}")

        status = "BROKEN" if r["overflow"] > 0 else ("warn" if r["wrapped"] else "ok")
        print(f"{status}: {name} overflow={r['overflow']}px wrapped={len(r['wrapped'])}")

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
