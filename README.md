# VCSS Website

Static skeleton for the Voiland College Student Resources site (`vcea.wsu.edu/student-success/`), built from the site plan.

- `_Scripts/build.py` — all page content + templates; run `.venv/bin/python _Scripts/build.py` from this folder. Regenerates `site/`.
- `site/` — generated output (open `site/index.html`). Don't hand-edit.
- `Assets/` — real photos (optimized copies; originals in `Assets/source/`). Anything here is copied into `site/img/` on build and overrides a same-named placeholder.
- `redirects.csv` / `site/_redirects` — old → new map.

`[TBD]` (yellow) and `[VERIFY]` (red) mark content the team must supply or confirm.
Remaining images are placeholders. The site is a draft: pages are `noindex` and `site/robots.txt` blocks crawlers until launch. See `AGENTS.md` for conventions.

## GitHub Pages

This folder is also the standalone `ssaunders9/vcss-website` repository. The
`site/` directory is the published static site. Pushes to `main` deploy it
through `.github/workflows/pages.yml`.

To rebuild locally before committing:

```text
/config/workspace/.venv/bin/python _Scripts/build.py
```
