"""Typeset each chapter of Inquiry and Practice as a Renaissance-styled PDF."""
import re, subprocess, sys, html, glob, os
from pathlib import Path
import numpy as np
from PIL import Image
import weasyprint

S = Path(sys.argv[1])          # scratchpad root
MD, FIG, FONTS = S/"md", S/"fig", S/"fonts"
OUT = Path(os.environ.get("OUTDIR", S/"site"/"chapters"))
TONE = Path(os.environ.get("TONEDIR", S/"figtone"))
OUT.mkdir(parents=True, exist_ok=True)
TONE.mkdir(exist_ok=True)

BOOK, AUTHOR = "Inquiry and Practice", "Anatoly Lezhen"
ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split()

# Palette: iron-gall ink, sanguine (red chalk), verdigris-indigo, paper
INK, SANG, INDIGO, FADED, PAPER = (os.environ.get(k, d) for k, d in (("C_INK","#2E2418"),("C_SANG","#9C4A2F"),("C_INDIGO","#3E5A68"),("C_FADED","#8C7457"),("C_PAPER","#FBF7EE")))

HAIR = os.environ.get("C_HAIR", "#D9CDB6")

def hexrgb(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)

def tone_figure(src, dst):
    """Re-ink a bright UI figure in the book's palette: blues -> indigo ink,
    oranges -> sanguine, neutrals -> sepia, white -> paper."""
    im = np.asarray(Image.open(src).convert("RGB")).astype(float) / 255
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mx, mn = im.max(-1), im.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = 0.299*r + 0.587*g + 0.114*b
    paper, ink = hexrgb(PAPER)/255, hexrgb(INK)/255
    # neutral base: duotone ink -> paper by luminance
    base = ink + (paper - ink) * lum[..., None]
    out = base.copy()
    blue = (b > r) & (sat > 0.05)
    warm = (r > b) & (sat > 0.05)
    for mask, col in ((blue, hexrgb(INDIGO)/255), (warm, hexrgb(SANG)/255)):
        # tint keeps the original lightness: light fills stay light washes
        w = np.clip((1 - lum) / 0.6, 0, 1)[..., None]
        tinted = paper + (col - paper) * np.clip(w * 1.05 + 0.08, 0, 1)
        out[mask] = tinted[mask]
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(dst)

ORNAMENT = f"""<svg class="orn" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="{SANG}" stroke-width="0.6">
<circle cx="60" cy="60" r="44"/><rect x="24" y="24" width="72" height="72" stroke="{FADED}"/>
<circle cx="60" cy="60" r="22" stroke="{FADED}" stroke-width="0.4"/>
<path d="M60 8 L60 112 M8 60 L112 60" stroke="{FADED}" stroke-width="0.3" stroke-dasharray="1.5 2.5"/>
<path d="M29 91 A44 44 0 0 1 91 29" stroke="{INK}" stroke-width="0.35"/>
<circle cx="60" cy="60" r="1.6" fill="{SANG}" stroke="none"/></svg>"""

CSS = f"""
@font-face {{ font-family: 'EB'; src: url('file://{FONTS}/EBGaramond[wght].ttf'); font-weight: 400 800; }}
@font-face {{ font-family: 'EB'; src: url('file://{FONTS}/EBGaramond-Italic[wght].ttf'); font-style: italic; font-weight: 400 800; }}
@font-face {{ font-family: 'Corm'; src: url('file://{FONTS}/CormorantGaramond[wght].ttf'); font-weight: 300 700; }}
@font-face {{ font-family: 'Corm'; src: url('file://{FONTS}/CormorantGaramond-Italic[wght].ttf'); font-style: italic; font-weight: 300 700; }}
@page {{ size: 6in 9in; margin: 0.85in 0.8in 0.9in 0.85in; background: {PAPER};
  @top-left {{ content: "{BOOK}"; font: italic 8pt 'EB'; color: {FADED}; }}
  @top-right {{ content: string(chtitle); font: 8pt 'EB'; color: {FADED}; letter-spacing: .06em; font-variant: small-caps; }}
  @bottom-center {{ content: counter(page); font: 8.5pt 'EB'; color: {SANG}; }} }}
@page :first {{ @top-left {{ content: none; }} @top-right {{ content: none; }} @bottom-center {{ content: none; }} }}
html {{ font-family: 'EB'; font-size: 10.6pt; line-height: 1.5; color: {INK};
  font-variant-numeric: oldstyle-nums; hyphens: auto; }}
body {{ margin: 0; }}
.opener {{ text-align: center; padding-top: .35in; page-break-after: avoid; }}
.opener .book {{ font: italic 9pt 'EB'; color: {FADED}; letter-spacing: .04em; }}
.orn {{ width: .95in; height: .95in; margin: .3in auto .22in; display: block; }}
.opener .num {{ font: 300 10pt 'Corm'; letter-spacing: .4em; color: {SANG}; margin-bottom: .08in; }}
h1 {{ font: 300 25pt/1.12 'Corm'; margin: 0 0 .05in; string-set: chtitle content(); color: {INK}; }}
.opener .sub {{ font: italic 300 13pt 'Corm'; color: {FADED}; margin-top: .02in; }}
.rule {{ width: 1.1in; border-top: .4pt solid {SANG}; margin: .22in auto .25in; }}
.epi {{ margin: 0 .35in .35in; text-align: center; }}
.epi p {{ font: italic 10pt/1.45 'EB'; margin: 0; }}
.epi .att {{ font: 8.5pt 'EB'; color: {FADED}; margin-top: .06in; font-style: normal; letter-spacing: .02em; }}
h2 {{ font: 400 14.5pt/1.2 'Corm'; color: {INK}; margin: 1.5em 0 .5em; page-break-after: avoid; letter-spacing: .01em; }}
h2::before {{ content: "❧ "; color: {SANG}; font-size: 10pt; }}
h3 {{ font: italic 500 12pt 'Corm'; color: {SANG}; margin: 1.2em 0 .3em; page-break-after: avoid; }}
p {{ margin: 0; text-align: justify; orphans: 2; widows: 2; }}
p + p {{ text-indent: 1.4em; }}
h2 + p::first-letter {{ font-family: 'Corm'; font-size: 1.55em; line-height: 1; color: {SANG}; }}
strong {{ font-weight: 600; }}
a {{ color: {SANG}; text-decoration: none; }}
sup {{ font-size: .62em; color: {SANG}; line-height: 0; }}
blockquote {{ margin: .9em 1.3em; padding-left: .8em; border-left: .4pt solid {SANG}; }}
blockquote p {{ text-indent: 0 !important; font-style: italic; }}
ul, ol {{ margin: .5em 0 .6em; padding-left: 1.5em; }} li {{ margin: .15em 0; }} li p {{ text-indent: 0 !important; }}
ol li::marker {{ color: {SANG}; }} ul li::marker {{ color: {SANG}; }}
table {{ border-collapse: collapse; width: 100%; margin: 1em 0 1.1em; font-size: 8.4pt; line-height: 1.35; page-break-inside: auto; }}
th {{ font-weight: 500; text-align: left; color: {SANG}; border-bottom: .5pt solid {SANG}; padding: .3em .45em; font-variant: small-caps; letter-spacing: .03em; }}
td {{ border-bottom: .3pt solid {HAIR}; padding: .32em .45em; vertical-align: top; text-align: left; }}
td p, th p {{ text-indent: 0 !important; text-align: left; }}
tr {{ page-break-inside: avoid; }}
figure {{ margin: 1.2em 0; text-align: center; page-break-inside: avoid; }}
figure img {{ width: 100%; }}
figcaption {{ font: italic 8.5pt 'EB'; color: {FADED}; margin-top: .4em; }}
.formula {{ text-align: center; font: italic 14pt 'Corm'; margin: .8em 0; color: {INK}; letter-spacing: .02em; text-indent: 0 !important; }}
.formula .op {{ color: {SANG}; font-style: normal; padding: 0 .25em; }}
hr {{ border: 0; border-top: .4pt solid {SANG}; width: 1in; margin: 1.5em auto; }}
.colophon {{ margin-top: 2.2em; text-align: center; font: italic 8.5pt 'EB'; color: {FADED}; text-indent: 0 !important; }}
"""

def mdtohtml(md):
    r = subprocess.run(["pandoc", "-f", "gfm-autolink_bare_uris", "-t", "html5", "--wrap=none"],
                       input=md, capture_output=True, text=True, check=True)
    return r.stdout

def build(n):
    raw = (MD/f"ch{n:02d}.md").read_text()
    lines = raw.split("\n")
    title = lines[0].lstrip("# ").strip()
    title = re.sub(r"^Chapter \d+:\s*", "", title)
    main, _, sub = title.partition(": ")
    body = "\n".join(lines[1:])
    body = re.sub(r"^.*· @Anatoly Lezhen\s*$", "", body, count=1, flags=re.M)
    # epigraph = first blockquote
    m = re.search(r"((?:^>.*\n?)+)", body, flags=re.M)
    epi_html = ""
    if m and m.start() < 400:
        q = [l[1:].strip() for l in m.group(1).strip().split("\n")]
        q = [l for l in q if l]
        quote, att = q[0], " ".join(q[1:])
        epi_html = f'<div class="epi">{mdtohtml(quote)}<div class="att">{mdtohtml(att).replace("<p>","").replace("</p>","")}</div></div>'
        body = body[:m.start()] + body[m.end():]
    # figures
    figs = sorted(glob.glob(str(FIG/f"ch{n:02d}-*.png")))
    k = 0
    def figrep(mm):
        nonlocal k
        cap = mm.group(1).strip()
        if k >= len(figs):
            k += 1
            return ""
        src = figs[k]; k += 1
        dst = TONE/Path(src).name
        tone_figure(src, dst)
        return f'\n<figure><img src="file://{dst}"/><figcaption>{html.escape(cap)}</figcaption></figure>\n'
    body = re.sub(r"^&#91;embedded content: (.*?)\\\]\s*$", figrep, body, flags=re.M)
    # formula
    body = re.sub(r"```latex\s*\n(.*?)\n```",
        lambda mm: '<p class="formula">Learning <span class="op">≈</span> Inquiry <span class="op">×</span> Practice</p>'
        if "Learning" in mm.group(1) else mm.group(0), body, flags=re.S)
    # note markers -> superscripts (not inside the Notes list itself)
    body = re.sub(r"\\\[(\d{1,2})\\\]", r"<sup>\1</sup>", body)
    content = mdtohtml(body)
    sub_html = f'<div class="sub">{html.escape(sub)}</div>' if sub else ""
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{BOOK}, Chapter {n}: {html.escape(main)}</title>
<meta name="author" content="{AUTHOR}"><style>{CSS}</style></head><body>
<div class="opener"><div class="book">{BOOK} · {AUTHOR}</div>{ORNAMENT}
<div class="num">CHAPTER {ROMAN[n-1]}</div><h1>{html.escape(main)}</h1>{sub_html}<div class="rule"></div>{epi_html}</div>
{content}
<p class="colophon">From <em>{BOOK}</em>, by {AUTHOR}. Working draft, {"October 2026"}.</p>
</body></html>"""
    slug = re.sub(r"[^a-z0-9]+", "-", main.lower()).strip("-")
    out = OUT/f"{n:02d}-{slug}.pdf"
    weasyprint.HTML(string=doc, base_url=str(S)).write_pdf(out)
    print(out.name, f"figs {k}/{len(figs)}")
    return out

if __name__ == "__main__":
    nums = [int(x) for x in sys.argv[2:]] or range(1, len(list((S/"md").glob("ch*.md"))) + 1)
    for n in nums: build(n)
