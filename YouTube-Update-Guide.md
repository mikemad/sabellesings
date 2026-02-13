# 🎵 YouTube Video Update Guide

The YouTube grid now refreshes itself every time the page loads. It looks at the channel handle defined in `index.html`, fetches the latest uploads straight from the YouTube RSS feed (via a privacy-friendly proxy), and swaps in fresh embeds automatically.

You only need to touch the files on disk in a few scenarios:

1. **Change which channel/handle or how many videos appear.**
2. **Update the curated fallback list** that is shown if YouTube is unreachable.
3. **Generate a brand-new fallback snippet** (optional) with `youtube-helper.html`.

---

## 1. Adjusting the feed settings

Open `index.html` and find the YouTube section:

```html
<section
  class="youtube-section"
  id="youtube"
  aria-labelledby="youtube-title"
  data-youtube-handle="@Sabellesings"
  data-youtube-max="6">
```

- `data-youtube-handle` – change this if you ever rebrand your handle.
- `data-youtube-max` – set how many of the latest uploads to render (best visual layout is 6).

> Tip: the script will automatically resolve the real Channel ID the first time it runs, so you never need to look it up manually.

---

## 2. Maintaining the fallback playlist

If YouTube is blocked or fails CORS checks, the site swaps to a baked-in set of videos stored inside `<template id="youtubeFallback">` in `index.html`. Update that list whenever you want to curate which videos appear during outages.

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
3. Click **“🚀 Generate HTML Code”** and copy the output.
4. Replace the contents of the `<template id="youtubeFallback">` in `index.html` with the new snippet.

---

## 4. Testing the experience

1. Open `index.html` locally.
2. Check that you see the “Auto-updated …” message underneath the YouTube heading—this means the live feed loaded.
3. Temporarily disconnect from the internet (or block `youtube.com`) to make sure the fallback template appears and the status message switches to the warning text.

That’s it! Everyday updates now happen automatically, and you only edit the fallback/template when you want to curate a specific set of showcase videos.
