# Agent Instructions — VCSS Website

> **Canonical instructions for every AI tool in this repo** (Copilot, Codex, Claude Code, etc.). Edit this file only — `CLAUDE.md` imports it and `.github/copilot-instructions.md` points here.

<!-- BEGIN SHARED — synced from the parent workspace AGENTS.md (https://github.com/ssaunders9/workspace).
     Edit the workspace copy first, then paste the same block into every nested repo's AGENTS.md. -->

## Workspace Conventions (shared)

This repo is part of a larger faculty workspace for teaching, department service, and research at WSU's Voiland School of Chemical Engineering and Bioengineering (VSCEB). The parent workspace repo is at `https://github.com/ssaunders9/workspace`.

### Naming (strictly enforced)

- **Underscores only, never spaces**: `CHE_441/`, `retention_analysis.py`, `syllabus_2026.pdf`
- **Meta/non-primary folders prefixed with `_`**: `_Archive/`, `_Drafts/`, `_Scripts/`
- **Content folders unprefixed**: `Syllabus/`, `Assets/`, `Canvas_Pages/`
- **Course codes**: space in code (`CHE 101`), underscore in folder name (`CHE_441/`)

### Response Style

**When asked what to work on, or when a session involves a multi-step task, always respond with a numbered list.** Each item should be one actionable thing. Do not combine multiple changes into one list item. The list is the working agenda — the user picks items from it to execute one at a time.

### Patterns

- **Backups are component-local with timestamped names** — never overwrite an existing backup.
- **`_Archive/` and `_Drafts/` are not authoritative** — always edit the non-prefixed sibling.
- **Before editing, inspect the nearby README, local scripts, and canonical source file** so changes match local conventions.
- **Do not consolidate duplicated images, reorganize archives, or clean generated files** unless explicitly asked.
- **Check before re-running a long or resource-heavy script** — confirm it isn't already running, rather than launching another one reflexively.
- **This is a separate git repo** — commit and push from this directory, not from the parent workspace.

<!-- END SHARED -->

## Project: VCSS Website

Static site skeleton for the Voiland College Student Resources site (planned for `vcea.wsu.edu/student-success/`). Not a copy of the current site: the structure follows the new site plan, and the current site was used only as a source of facts and images.

**Remote**: `https://github.com/ssaunders9/vcss-website` (public). Pushes to `main` deploy `site/` to GitHub Pages via `.github/workflows/pages.yml`.

## How it is built

- `_Scripts/build.py` holds every page's content plus the templates, CSS and JS. Run `/config/workspace/.venv/bin/python _Scripts/build.py` from this folder; it regenerates `site/`.
- **Never hand-edit `site/`**; edit `build.py` (or `_Scripts/clubs.json`) and rebuild, then commit the regenerated `site/`.
- `Assets/` holds real photos (flat, optimized); `Assets/source/` holds the downloaded originals. Files in `Assets/` are copied into `site/img/` on build.
- CSS is one string in `build.py`, built in order: later blocks override earlier ones. Append new rules at the end, not at the top.
- `VCEA_Student_Success_Content_Capture.md` is the raw capture of the current site; use it as a fact source, do not copy prose.

## Conventions

- `[TBD: ...]` marks content the team must supply and `[VERIFY: ...]` marks conflicting facts on the current site. Both render highlighted; leave them until resolved.
- No emoji, em dashes, arrows or decorative glyphs in page copy.
- Style: WSU look (crimson `#A60F2D`, bright crimson `#CA1237`, ink `#262626`, light gray `#F2F2F2`, Montserrat). Light mode only.
- Menus collapsible; keep the Home page usable without scrolling on a laptop screen.

## Publishing guard

The site is a draft: every page has `noindex, nofollow` and `site/robots.txt` disallows all crawlers. Remove both only when the site is ready to launch. Tutor photos and staff contact details are republished from the current site; confirm permission before launch.
