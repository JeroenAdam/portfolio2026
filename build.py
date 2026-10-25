"""Build the portfolio for production — no Babel on the site.

index.html is the single source of truth: it runs the app through in-browser
Babel (great for editing, slow for visitors). This script extracts the app
code, compiles + minifies it with esbuild (standalone binary, no Node.js
needed — auto-downloaded from the npm registry on first run), and assembles
dist/ ready for Netlify.

Usage:  python build.py

Output: dist/  (drag & drop to Netlify, or publish dir "dist")
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(ROOT, "tools")
DIST = os.path.join(ROOT, "dist")
ESBUILD = os.path.join(TOOLS, "esbuild.exe")
ESBUILD_NPM = "0.28.2"

COPY_FILES = ["data.json", "custom-pmtool.mp4", "_headers", "_redirects", "robots.txt"]
COPY_DIRS = ["images", "svg"]

SITE_ORIGIN = "https://www.adambahri.com"
STATIC_PAGES = ["/", "/about", "/projects", "/blog", "/myvoyages", "/myboat",
                "/contact", "/video", "/skillmatrix", "/bookkeeping-app"]


def generate_sitemap(data):
    """sitemap.xml: every route + all blog articles (lastmod = created date)."""
    urls = ['  <url>\n    <loc>%s%s</loc>\n  </url>' % (SITE_ORIGIN, p)
            for p in STATIC_PAGES]
    for post in data.get("blogs", []):
        if not post.get("slug"):
            continue
        lastmod = (post.get("created") or "")[:10]
        entry = '  <url>\n    <loc>%s/blogs/%s</loc>' % (SITE_ORIGIN, post["slug"])
        if lastmod:
            entry += '\n    <lastmod>%s</lastmod>' % lastmod
        urls.append(entry + "\n  </url>")
    body = "\n".join(urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '%s\n</urlset>\n' % body)


def ensure_esbuild():
    """Have the esbuild binary; download the win32-x64 npm package if missing."""
    if os.path.exists(ESBUILD):
        return
    os.makedirs(TOOLS, exist_ok=True)
    url = (
        "https://registry.npmjs.org/@esbuild/win32-x64/-/"
        "win32-x64-%s.tgz" % ESBUILD_NPM
    )
    print("Downloading esbuild %s ..." % ESBUILD_NPM)
    data = urllib.request.urlopen(url).read()
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        with tf.extractfile("package/esbuild.exe") as f:
            with open(ESBUILD, "wb") as out:
                shutil.copyfileobj(f, out)


def extract_app(html):
    """Return the inline text/babel block (the whole app)."""
    m = re.search(
        r'<script type="text/babel"[^>]*>\n(.*?)\n  </script>', html, re.S
    )
    if not m:
        sys.exit("ERROR: could not find the inline text/babel script in index.html")
    return m.group(1)


def production_html(html):
    """Swap the Babel setup for the compiled bundle."""
    # drop Babel itself
    html = re.sub(
        r" *<script src=\"https://unpkg\.com/@babel/standalone[^\"]*\"></script>\n",
        "",
        html,
    )
    # inline JSX block -> compiled bundle
    html = re.sub(
        r'  <script type="text/babel"[^>]*>.*?</script>\n',
        '  <script defer src="/app.min.js"></script>\n',
        html,
        flags=re.S,
    )
    # CDN libs: defer keeps execution order but unblocks HTML parsing
    html = re.sub(
        '<script (crossorigin )?src="(https://[^"]+)"></script>',
        lambda m: '<script %sdefer src="%s"></script>' % (m.group(1) or "", m.group(2)),
        html,
    )
    html = html.replace(
        "React 18 + Babel (single-file setup, no build step)",
        "React 18 (production build: app code pre-compiled by build.py)",
    )
    return html


def main():
    ensure_esbuild()
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read()

    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    src = os.path.join(TOOLS, "app.src.jsx")
    with open(src, "w", encoding="utf-8") as f:
        f.write(extract_app(html))

    # classic JSX transform: emits React.createElement (React stays the CDN global)
    subprocess.run(
        [
            ESBUILD,
            src,
            "--loader:.jsx=jsx",
            "--jsx=transform",
            "--target=es2018",
            "--minify",
            "--legal-comments=none",
            "--outfile=" + os.path.join(DIST, "app.min.js"),
        ],
        check=True,
    )

    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write(production_html(html))

    for name in COPY_FILES:
        shutil.copy2(os.path.join(ROOT, name), os.path.join(DIST, name))
    for name in COPY_DIRS:
        shutil.copytree(os.path.join(ROOT, name), os.path.join(DIST, name))

    with open(os.path.join(ROOT, "data.json"), encoding="utf-8") as f:
        data = json.load(f)
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(generate_sitemap(data))
    print("  sitemap.xml %d urls" % (len(STATIC_PAGES) + len(data.get("blogs", []))))

    total = 0
    for dirpath, _, files in os.walk(DIST):
        for fn in files:
            total += os.path.getsize(os.path.join(dirpath, fn))
    app_js = os.path.getsize(os.path.join(DIST, "app.min.js"))
    print("Built dist/:")
    print("  app.min.js  %s KB (compiled JSX, minified)" % round(app_js / 1024, 1))
    print("  dist total  %s KB incl. images/media" % round(total / 1024, 1))
    print("Deploy: drag & drop the dist folder to Netlify,")
    print("        or publish dir 'dist' with empty build command.")


if __name__ == "__main__":
    main()
