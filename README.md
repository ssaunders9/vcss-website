# VCSS Website

Static skeleton for the Voiland College Student Resources site (`vcea.wsu.edu/student-success/`), built from the site plan.

- `_Scripts/build.py` — all page content + templates; run `.venv/bin/python _Scripts/build.py` from this folder. Regenerates `site/`.
- `site/` — generated output (open `site/index.html`). Don't hand-edit.
- `Assets/` — drop real photos here named like the placeholders (e.g. `hero.svg` → use same filename, or edit `IMAGES`/img refs); they overwrite placeholders in `site/img/`.
- `redirects.csv` / `site/_redirects` — old → new map.

`[TBD]` (yellow) and `[VERIFY]` (red) mark content the team must supply or confirm.
Images are placeholders: vcea.wsu.edu blocks automated downloads (HTTP 403), so use WSU-approved photography.

## GitHub Pages

This folder is also the standalone `ssaunders9/vcss-website` repository. The
`site/` directory is the published static site. Pushes to `main` deploy it
through `.github/workflows/pages.yml`.

To rebuild locally before committing:

```text
/config/workspace/.venv/bin/python _Scripts/build.py
```
