# Inquiry and Practice

The website for *Inquiry and Practice* by Anatoly Lezhen, live at https://inquiryandpractice.com

Cloudflare publishes the `site/` folder as is: `wrangler.jsonc` points Cloudflare Workers at it, and a Pages project uses `site` as its build output directory. There is no build command. Every push to `main` goes live in about a minute.

| Folder | What it holds |
| --- | --- |
| `site/` | The published website: `index.html` (home page and reading view), chapter PDFs in two color schemes, the reading-view chapters, and the share image |
| `source/md/` | Each chapter's text, exported from the manuscript |
| `source/fig/` | Each chapter's figures, as exported from the manuscript |
| `source/page/index.html` | The page itself, before packaging |
| `source/fonts/`, `source/brand/` | Garamond fonts (SIL Open Font License) for the PDFs, and the share image |
| `tools/` | The scripts that typeset the PDFs, build the reading view, and package `site/` |

## Updating

- **A podcast link or page text:** edit `source/page/index.html`, then run `tools/rebuild.sh inquiryandpractice.com`.
- **A revised chapter:** replace its file in `source/md/` (and any figure in `source/fig/`), then run `tools/rebuild.sh inquiryandpractice.com`.
