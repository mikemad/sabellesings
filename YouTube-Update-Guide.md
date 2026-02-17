# 🎵 YouTube Video Update Guide

The YouTube grid refreshes itself every time the page loads. A GitHub Actions workflow fetches the latest uploads from the YouTube RSS feed every 6 hours and commits `youtube-feed.xml` to the repo. The page loads that local file directly — no CORS proxies needed.

You only need to touch the files on disk in a few scenarios:

1. **Change how many videos appear.**
2. **Update the curated fallback list** that is shown if the feed is unavailable.
3. **Generate a brand-new fallback snippet** (optional) with `youtube-helper.html`.

---

## 1. Adjusting the feed settings

Open `index.html` and find the YouTube section:

```html
<section
  class="youtube-section"
  id="youtube"
  aria-labelledby="youtube-title"
  data-youtube-max="6">
```

- `data-youtube-max` – set how many of the latest uploads to render (best visual layout is 6).

The channel ID is configured in `.github/workflows/fetch-youtube-feed.yml`.

---

## 2. Maintaining the fallback playlist

If the feed file is missing or fails to load, the site swaps to a baked-in set of videos stored inside `<template id="youtubeFallback">` in `index.html`. Update that list whenever you want to curate which videos appear during outages.

Each entry follows this structure:

```html
<div class="video-card">
  <div class="video-embed">
    <iframe src="https://www.youtube-nocookie.com/embed/VIDEO_ID?rel=0&modestbranding=1"
            title="Video title - Sabelle"
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen></iframe>
  </div>
  <p class="video-title">Video title - Sabelle</p>
</div>
```

Keep six fallback cards so the layout stays balanced. You can paste iframe code directly or generate it with the helper tool below.

---

## 3. Using the helper tool (optional)

`youtube-helper.html` still lives in the repo for quick copy/paste work:

1. Open it in your browser.
2. Enter any YouTube URLs and titles (the helper extracts the IDs for you).
3. Click **"🚀 Generate HTML Code"** and copy the output.
4. Replace the contents of the `<template id="youtubeFallback">` in `index.html` with the new snippet.

---

## 4. Testing the experience

1. Open `index.html` locally.
2. Check that you see the "Showing the latest uploads" message underneath the YouTube heading — this means the feed loaded.
3. Rename or delete `youtube-feed.xml` temporarily to make sure the fallback template appears and the status message switches to the warning text.

That's it! The feed is updated automatically by GitHub Actions, and you only edit the fallback/template when you want to curate a specific set of showcase videos.
