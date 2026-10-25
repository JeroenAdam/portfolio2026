# Single-page portfolio (React)

Classic, business-styled portfolio: the app lives in **one HTML file** plus a
**static JSON data file**. During development the JSX runs through in-browser
Babel (instant editing, no pipeline); for production `build.py` pre-compiles
it to a minified bundle so visitors never touch Babel.

Repository: https://github.com/JeroenAdam/portfolio2026 — the live source of
https://www.adambahri.com. It replaces the previous Gatsby implementation,
archived at https://github.com/JeroenAdam/portfolio. The app is at the repo
root, so Netlify's publish directory is simply `dist`.

## Files

| File | Purpose |
|---|---|
| `index.html` | The whole app (markup + CSS + JSX components) and the dev entry point. React 18 + marked + Font Awesome load from CDNs. **Edit this.** |
| `data.json` | All content that used to come from Contentful: profile, skills, jobs, projects, blogs (56 articles), about, boat, voyages slides. |
| `images/` | Hero image, voyage slides, myboat photos, and the ~120 photos referenced inside blog articles. **All images are self-hosted** — no external image hosts. Photos are WebP (q95), PNG-derived graphics lossless WebP. Pre-conversion originals live on a backup drive (were in `captured/`). |
| `svg/` | Tool icons used in the "About me → toolset" panel. |
| `custom-pmtool.mp4` | Demo video for the Collaboration Workspace project. |
| `serve.py` | Dev server: no-cache headers + SPA fallback for path URLs (`/blogs/foo`). |
| `build.py` | Production build → `dist/` (see below). Downloads the esbuild binary into `tools/` on first run (no Node.js needed). |
| `_headers` / `_redirects` | Netlify config: cache rules + SPA fallback. |
| `robots.txt` | Tells crawlers to index everything; points to the sitemap. |
| `sitemap.xml` | Generated into `dist/` on every build: all pages + all blog articles with lastmod dates. |
| `build_data.py` | One-off migration script that rebuilt `data.json` from the original Gatsby page-data snapshots. Those snapshots plus the pre-conversion image originals are archived on a backup drive (they used to sit in `captured/`). |

## Run locally (development)

```
python serve.py 8080
```

then open http://localhost:8080. Edit `index.html` / `data.json`, reload, done.
Browsers block `fetch()` on `file://` pages, so serving over HTTP is required.

## Build & deploy

```
python build.py
```

`build.py` extracts the app code from `index.html`, compiles + minifies it
with esbuild (standalone binary, auto-downloaded once into `tools/`), and
assembles **`dist/`**:

- `index.html` — Babel removed, app code replaced by `<script defer
  src="/app.min.js">` (all scripts deferred, order preserved)
- `app.min.js` — compiled + minified app (~26 KB)
- copies of `data.json`, `images/`, `svg/`, `custom-pmtool.mp4`,
  `_headers`, `_redirects`

Deploy `dist/` to Netlify:

- **Drag & drop**: drag the `dist` folder to app.netlify.com/drop
- **Git**: build command *empty*, publish directory `dist`

`_redirects` serves `index.html` for every path, so old Gatsby-style URLs
(`/blogs/some-article`) work as direct entry points; the router normalizes
the address bar to the clean path form. `_headers` keeps `index.html` and
`data.json` fresh while caching media for 30 days.

## Editing content

Open `data.json`:

- `services` — the six "My skills" cards
- `jobs` — experience tabs (markdown allowed in `desc`)
- `projects` — shown on Home (where `featured: true`) and on the Projects page
- `blogs` — articles; `content` is markdown (mixed inline HTML is fine,
  the lightbox popups work as before)
- `about`, `myboat`, `voyages`, `profile`, `navigation` — as their names say

Images referenced in blog `content` are expected under `images/`.
For new blog covers, put the file in `images/` too (keep the site free of
external image dependencies); convert to WebP with Pillow:
`img.save("x.webp", "WEBP", quality=95, method=6)` for photos,
`lossless=True` for graphics/screenshots.

## Routes

Path URLs, exactly as Google indexed them on the old Gatsby site:
`/`, `/about`, `/projects`, `/blog`, `/blogs/<slug>`, `/myvoyages`,
`/myboat`, `/contact`, `/video`, `/skillmatrix`, `/bookkeeping-app`, plus a
404 fallback. Old `/#/route` links still work and are normalized to
`/route`. In-page anchors and lightboxes (`/projects#some-project-full`)
stay hash-based.

## What changed vs. the Gatsby version

- Contentful → static `data.json`; Gatsby GraphQL → simple `fetch`.
  All Contentful-hosted images are now downloaded and served from `images/`
  (WebP); the site has zero external image dependencies.
  Gatsby-generated `/static/...` hashes (which only existed in the old
  build) were replaced by real files copied into `images/`.
- Internal links to `https://www.adambahri.com/...` in content were
  rewritten to routes; the contact form still posts to the same Formspree
  endpoint.
- Dark mode: moon/sun toggle in the header; saved in `localStorage`,
  first-time visitors follow `prefers-color-scheme`. Applied before first
  paint by a tiny inline script (no flash).
- Project photos and the myboat photo open in a full-screen lightbox
  (CSS `:target`, no route change; click the overlay to close).
- The experience section keeps a constant height: all job panels are
  stacked in one grid cell, so the container always fits the tallest one.
