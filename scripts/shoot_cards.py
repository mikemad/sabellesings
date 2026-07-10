#!/usr/bin/env python3
"""Screenshot the generated cards into PNGs at exact Instagram dimensions.

Takes a path to Chrome (or Playwright's headless_shell). CI passes the
preinstalled google-chrome; locally any Chromium build works, so the same code
runs in both places.

Usage: shoot_cards.py <path-to-chrome>
"""

import os
import struct
import subprocess
import sys

# (source html, width, height, output png)
CARDS = [
    ("gigs/card-post.html", 1080, 1350, "gigs/gig-card.png"),
    ("gigs/card-story.html", 1080, 1920, "gigs/gig-card-story.png"),
]


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def main():
    if len(sys.argv) < 2:
        print("usage: shoot_cards.py <path-to-chrome>")
        return 1
    chrome = sys.argv[1]

    for src, w, h, out in CARDS:
        subprocess.run(
            [
                chrome, "--headless", "--disable-gpu", "--no-sandbox",
                "--hide-scrollbars", "--force-device-scale-factor=1",
                # Give the webfonts time to land; a miss would silently change metrics.
                "--virtual-time-budget=20000",
                f"--window-size={w},{h}",
                f"--screenshot={os.path.abspath(out)}",
                f"file://{os.path.abspath(src)}",
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        if not os.path.exists(out):
            print(f"FAIL: {chrome} produced no {out}")
            return 1
        got = png_size(out)
        if got != (w, h):
            print(f"FAIL: {out} is {got[0]}x{got[1]}, expected {w}x{h}")
            return 1
        print(f"ok: {out} {w}x{h} ({os.path.getsize(out) // 1024}KB)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
