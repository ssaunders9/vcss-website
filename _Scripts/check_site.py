#!/usr/bin/env python3
"""Static checks on the built site: broken internal links, image alt text, one h1 per page,
labelled form controls, and WCAG contrast for the palette. Run after build.py:
    /config/workspace/.venv/bin/python _Scripts/check_site.py
"""
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
problems = []

for f in sorted(SITE.rglob("*.html")):
    t = f.read_text()
    rel = f.relative_to(SITE)
    for h in re.findall(r'(?:href|src)="([^"#:]+)"', t):
        h = h.split("?")[0]
        if h:
            x = f.parent / h
            if x.is_dir(): x = x / "index.html"
            if not x.exists(): problems.append(f"{rel}: broken link {h}")
    for img in re.findall(r"<img\b[^>]*>", t):
        if "alt=" not in img: problems.append(f"{rel}: image without alt: {img[:80]}")
    n_h1 = len(re.findall(r"<h1\b", t))
    if n_h1 != 1: problems.append(f"{rel}: {n_h1} h1 headings")
    ids = set(re.findall(r'<label[^>]*for="([^"]+)"', t))
    for ctl in re.findall(r"<(?:input|select|textarea)\b[^>]*>", t):
        m = re.search(r'id="([^"]+)"', ctl)
        if 'type="hidden"' not in ctl and (not m or m.group(1) not in ids) and "aria-label" not in ctl:
            problems.append(f"{rel}: unlabelled control {ctl[:60]}")

def lum(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
PAIRS = [("body text", "#262626", "#FFFFFF"), ("body text on gray", "#262626", "#F2F2F2"), ("link crimson on white", "#A60F2D", "#FFFFFF"),
         ("link crimson on gray", "#A60F2D", "#F2F2F2"), ("secondary gray on white", "#595959", "#FFFFFF"), ("secondary gray on gray", "#595959", "#F2F2F2"),
         ("white on crimson button", "#FFFFFF", "#A60F2D"), ("white on bright crimson", "#FFFFFF", "#CA1237"), ("white on charcoal footer", "#FFFFFF", "#333333")]
for name, fg, bg in PAIRS:
    r = ratio(fg, bg)
    print(f"contrast {r:5.2f}  {'ok ' if r >= 4.5 else 'LOW'}  {name}")
    if r < 4.5: problems.append(f"contrast {name} {r:.2f} < 4.5")

print(f"\n{len(problems)} problem(s)")
for p_ in problems: print(" -", p_)
