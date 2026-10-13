"""Package the book site as a standalone static website for Cloudflare Pages.
Usage: make_dist.py <scratchpad> <out-dir> <domain>"""
import sys, shutil, html
from pathlib import Path

S, OUT, DOMAIN = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3].strip().lower()
SITE = S / "site"
URL = f"https://{DOMAIN}/" if DOMAIN not in ("", "-") else ""
OUT.mkdir(parents=True, exist_ok=True)
for d in ("chapters", "chapters-white", "reader"):
    if (OUT / d).exists():
        shutil.rmtree(OUT / d)
    shutil.copytree(SITE / d, OUT / d)
shutil.copy(S / "brand" / "og.png", OUT / "og.png")

body = (SITE / "index.html").read_text()
title_end = body.index("</title>") + len("</title>")
WORDS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
nch = len(list((SITE / "reader").glob("ch*.json")))
desc = f"Inquiry and Practice, a new model of human development by Anatoly Lezhen. Read all {WORDS[nch] if nch < len(WORDS) else nch} chapters free, or listen to the podcast."
CANON = f'<link rel="canonical" href="{URL}">\n' if URL else ""
OGURL = f'<meta property="og:url" content="{URL}">\n' if URL else ""
head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{body[:title_end]}
<meta name="description" content="{html.escape(desc)}">
<meta name="author" content="Anatoly Lezhen">
{CANON}<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta name="theme-color" content="#F5EFE2">
<meta property="og:type" content="book">
<meta property="og:site_name" content="Inquiry and Practice">
<meta property="og:title" content="Inquiry and Practice, by Anatoly Lezhen">
<meta property="og:description" content="{html.escape(desc)}">
{OGURL}<meta property="og:image" content="{URL or ''}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{URL or ''}og.png">
<style>
:root {{ padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>"""
rest = body[title_end:]
# drop the artifact-only description line; the head above carries the real one
rest = "\n".join(l for l in rest.split("\n") if not l.startswith('<meta name="description"'))
# head ends where the page's own <style> block ends
style_end = rest.index("</style>") + len("</style>")
page = head + rest[:style_end] + "\n</head>\n<body>\n" + rest[style_end:].lstrip("\n") + "\n</body>\n</html>\n"
(OUT / "index.html").write_text(page)

(OUT / "favicon.svg").write_text("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="12" fill="#F5EFE2"/>
<circle cx="23" cy="32" r="13" fill="none" stroke="#3B6064" stroke-width="3"/>
<circle cx="41" cy="32" r="13" fill="none" stroke="#9A472C" stroke-width="3"/>
<circle cx="32" cy="32" r="2.6" fill="#9A472C"/>
</svg>
""")
(OUT / "_headers").write_text("""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin

/index.html
  Cache-Control: public, max-age=0, must-revalidate

/reader/*
  Cache-Control: public, max-age=300

/chapters/*
  Cache-Control: public, max-age=3600

/chapters-white/*
  Cache-Control: public, max-age=3600
""")
(OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n" + (f"Sitemap: {URL}sitemap.xml\n" if URL else ""))
URL and (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{URL}</loc></url></urlset>\n')
(OUT / "README.md").write_text(f"""# Inquiry and Practice

The website for *Inquiry and Practice* by Anatoly Lezhen, served at {URL or "its custom domain"}

A static site with no build step. Cloudflare Pages publishes this repository as is; every push to `main` goes live in about a minute.

- `index.html`: the whole site (home page and reading view)
- `reader/`: each chapter's text for the reading view, and its figures in three color schemes
- `chapters/`, `chapters-white/`: the chapter PDFs for the Parchment and White schemes
- `og.png`: the image shown when the link is shared
""")
print("built", OUT, "for", URL)
