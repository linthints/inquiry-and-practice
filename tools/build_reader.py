"""Web edition of Inquiry and Practice: one JSON file per chapter plus figures
re-inked for each site scheme (parchment, parchment at night, white)."""
import re, subprocess, sys, json, glob, html
from pathlib import Path
import numpy as np
from PIL import Image

S = Path(sys.argv[1])
MD, FIG, OUT = S/"md", S/"fig", S/"site"/"reader"
SCHEMES = {  # paper, ink, Practice tint, Inquiry tint
    "p":  ("#F5EFE2", "#2B2117", "#9A472C", "#3B6064"),
    "pd": ("#1D1914", "#E8DEC9", "#D27A5A", "#8DB3B3"),
    "w":  ("#FFFFFF", "#231C15", "#7A4B2B", "#2D5592"),
}
for k in SCHEMES: (OUT/"fig"/k).mkdir(parents=True, exist_ok=True)

def rgb(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float) / 255

def tone(src, dst, paper, ink, warm_c, cool_c):
    im = np.asarray(Image.open(src).convert("RGB")).astype(float) / 255
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mx, mn = im.max(-1), im.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = 0.299*r + 0.587*g + 0.114*b
    P, I = rgb(paper), rgb(ink)
    out = I + (P - I) * lum[..., None]
    w = np.clip((1 - lum) / 0.6, 0, 1)[..., None]
    for mask, col in (((b > r) & (sat > .05), rgb(cool_c)), ((r > b) & (sat > .05), rgb(warm_c))):
        t = P + (col - P) * np.clip(w * 1.05 + .08, 0, 1)
        out[mask] = t[mask]
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    if img.width > 1200:
        img = img.resize((1200, round(img.height * 1200 / img.width)), Image.LANCZOS)
    img.quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(dst, optimize=True)

def pandoc(md, n):
    r = subprocess.run(["pandoc", "-f", "gfm-autolink_bare_uris", "-t", "html5", "--wrap=none",
                        f"--id-prefix=c{n}-"], input=md, capture_output=True, text=True, check=True)
    return r.stdout

index = []
for n in range(1, 16):
    raw = (MD/f"ch{n:02d}.md").read_text()
    lines = raw.split("\n")
    title = re.sub(r"^Chapter \d+:\s*", "", lines[0].lstrip("# ").strip())
    main, _, sub = title.partition(": ")
    body = "\n".join(lines[1:])
    body = re.sub(r"^.*· @Anatoly Lezhen\s*$", "", body, count=1, flags=re.M)
    epi = None
    m = re.search(r"((?:^>.*\n?)+)", body, flags=re.M)
    if m and m.start() < 400:
        q = [l[1:].strip() for l in m.group(1).strip().split("\n")]
        q = [l for l in q if l]
        strip = lambda h: re.sub(r"^<p>|</p>\s*$", "", h.strip())
        epi = {"quote": strip(pandoc(q[0], n)), "cite": strip(pandoc(" ".join(q[1:]), n))}
        body = body[:m.start()] + body[m.end():]
    figs = sorted(glob.glob(str(FIG/f"ch{n:02d}-*.png")))
    k = 0
    def figrep(mm):
        global k
        cap = mm.group(1).strip()
        if k >= len(figs):
            k += 1; return ""
        name = Path(figs[k]).name; k += 1
        for key, pal in SCHEMES.items():
            tone(figs[k-1], OUT/"fig"/key/name, *pal)
        alt = html.escape(cap)
        imgs = "".join(f'<img class="fig-{key}" src="reader/fig/{key}/{name}" alt="{alt}" loading="lazy">' for key in SCHEMES)
        return f'\n<figure class="plate-fig">{imgs}<figcaption>{alt}</figcaption></figure>\n'
    body = re.sub(r"^&#91;embedded content: (.*?)\\\]\s*$", figrep, body, flags=re.M)
    body = re.sub(r"```latex\s*\n(.*?)\n```",
        lambda mm: '<p class="r-formula">Learning <span class="op">≈</span> <span class="i">Inquiry</span> <span class="op">×</span> <span class="p">Practice</span></p>'
        if "Learning" in mm.group(1) else mm.group(0), body, flags=re.S)
    body = re.sub(r"\\\[(\d{1,2})\\\]", r"<sup>\1</sup>", body)
    content = pandoc(body, n)
    content = re.sub(r"<table>", '<div class="r-table"><table>', content).replace("</table>", "</table></div>")
    content = content.replace('<a href="http', '<a target="_blank" rel="noopener" href="http')
    words = len(re.sub(r"<[^>]+>", " ", content).split())
    data = {"n": n, "title": main, "sub": sub or None, "epigraph": epi, "html": content, "minutes": round(words / 230)}
    (OUT/f"ch{n:02d}.json").write_text(json.dumps(data, ensure_ascii=False))
    index.append((n, main, words, k))
for row in index: print(row)
