#!/usr/bin/env python3
"""Build the WRF-Fire manual: src/*.md + src/diagrams/*.svg -> docs/*.html.

Usage: python3 tools/build.py
Each page in src/ starts with a header block between '---' lines (title, kicker, lead).
Diagrams are included with a line:  {{fig:name|Caption text}}  (name = src/diagrams/name.svg)
Callouts:  <div class="note" markdown="1"> ... </div>  (note, warn, good, key)
"""
import html
import pathlib
import re
import shutil

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "docs"

NAV = [
    ("Start", [
        ("index", "Overview"),
    ]),
    ("The manual: WPS to WRF-Fire", [
        ("env", "Phase 0 · Environment and data"),
        ("domain", "Phase 1 · Domain design"),
        ("geogrid", "Phase 2 · Static data (geogrid)"),
        ("ungrib", "Phase 3 · Weather (ungrib)"),
        ("metgrid", "Phase 4 · Merge (metgrid)"),
        ("real", "Phase 5 · real.exe and namelist.input"),
        ("fire", "Phase 6 · The fire model"),
        ("moisture", "Fuel moisture in depth"),
        ("extend", "Other research inputs"),
        ("run", "Running it on Slurm"),
        ("reference", "Reference and failures"),
    ]),
    ("Running it safely", [
        ("gates", "The gating system"),
        ("example", "Worked example: every fire"),
    ]),
    ("Our work on CCR", [
        ("setup", "WPS on CCR: setup so far"),
        ("fuelmatch", "The fuel-map mismatch"),
        ("campaign", "The scaling campaign"),
        ("scaling", "Scaling and the elbow"),
        ("costmodel", "Cost model and node formula"),
        ("queue", "Queue waits and cost"),
        ("lessons", "What went wrong, what we learnt"),
        ("design", "The workflow we designed"),
    ]),
]

# Pages kept in src/ but not published for now (the "Our work on CCR" section).
HIDDEN = {"setup", "fuelmatch", "campaign", "scaling", "costmodel", "queue", "lessons", "design"}
NAV = [(g, [(s, t) for s, t in items if s not in HIDDEN]) for g, items in NAV]
NAV = [(g, items) for g, items in NAV if items]

FLAT = [slug for _, items in NAV for slug, _ in items]
TITLES = {slug: t for _, items in NAV for slug, t in items}

LOGO = """<svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><rect width="30" height="30" rx="8" fill="#b4501f"/><path d="M15 5c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-7 0 3 1 4 2 4 0-3 0-6 1-9z" fill="#f6e2d5"/></svg>"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · WRF-Fire Manual</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<script>try{{var t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
</head>
<body>
<div class="topbar"><a href="index.html">WRF-Fire Manual</a><button type="button" onclick="document.querySelector('.side').classList.add('open')">Menu</button></div>
<div class="layout">
<nav class="side" aria-label="Site">
<button type="button" class="close" onclick="this.parentNode.classList.remove('open')">Close</button>
<a class="brand" href="index.html">{logo}<b>WRF-Fire Manual<span>WPS → WRF on UB CCR</span></b></a>
{nav}
<button type="button" class="theme-btn" onclick="toggleTheme()">Light / dark</button>
</nav>
<main>
<article class="page">
<p class="kicker">{kicker}</p>
<h1>{title}</h1>
<p class="lead">{lead}</p>
{toc}
{body}
{pager}
<footer class="foot">Checked against the WRF 4.6.0 and WPS 4.6 source. Built from <code>src/{slug}.md</code>.</footer>
</article>
</main>
</div>
<script>
function toggleTheme(){{var d=document.documentElement;var cur=d.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');var nx=cur==='dark'?'light':'dark';d.setAttribute('data-theme',nx);try{{localStorage.setItem('theme',nx);}}catch(e){{}}}}
</script>
</body>
</html>
"""


def parse(path):
    text = path.read_text()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def figures(text):
    def rep(m):
        name, cap = m.group(1), m.group(2)
        cls = ""
        if name.endswith("!small"):
            name, cls = name[:-6], ' class="small"'
        svg = (SRC / "diagrams" / f"{name}.svg").read_text().strip()
        cap_html = markdown.markdown(cap).removeprefix("<p>").removesuffix("</p>")
        return f'\n<figure{cls}><div class="fig">{svg}</div><figcaption>{cap_html}</figcaption></figure>\n'
    return re.sub(r"^\{\{fig:([\w!-]+)\|(.*?)\}\}\s*$", rep, text, flags=re.M)


def slugify(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(s).lower()).strip("-")


def nav_html(cur):
    out = []
    i = 0
    for group, items in NAV:
        out.append(f"<h4>{group}</h4><ol>")
        for slug, title in items:
            n = "" if slug == "index" else str(i)
            on = ' class="on"' if slug == cur else ""
            out.append(f'<li><a href="{slug}.html"{on}><span class="n">{n}</span><span>{title}</span></a></li>')
            if slug != "index":
                i += 1
        out.append("</ol>")
    return "\n".join(out)


def build():
    OUT.mkdir(exist_ok=True)
    shutil.copy(ROOT / "static" / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").write_text("")
    for h in HIDDEN:
        (OUT / f"{h}.html").unlink(missing_ok=True)
    for slug in FLAT:
        meta, text = parse(SRC / f"{slug}.md")
        text = figures(text)
        body = markdown.markdown(text, extensions=["tables", "fenced_code", "md_in_html", "attr_list"])
        body = re.sub(r'<a href="(%s)\.html[^"]*">(.*?)</a>' % "|".join(sorted(HIDDEN)), r"\2", body)
        body = re.sub(r"<table>", '<div class="tbl"><table>', body)
        body = body.replace("</table>", "</table></div>")
        heads = []

        def h2(m):
            inner = m.group(1)
            hid = slugify(inner)
            heads.append((hid, re.sub(r"<[^>]+>", "", inner)))
            return f'<h2 id="{hid}">{inner}</h2>'
        body = re.sub(r"<h2>(.*?)</h2>", h2, body)
        body = re.sub(r"<h3>(.*?)</h3>", lambda m: f'<h3 id="{slugify(m.group(1))}">{m.group(1)}</h3>', body)
        toc = ""
        if len(heads) >= 4 and meta.get("toc", "yes") != "no":
            toc = '<nav class="toc"><b>On this page</b><ul>' + "".join(
                f'<li><a href="#{h}">{t}</a></li>' for h, t in heads) + "</ul></nav>"
        idx = FLAT.index(slug)
        prev_l = f'<a class="prev" href="{FLAT[idx-1]}.html"><small>Previous</small>{TITLES[FLAT[idx-1]]}</a>' if idx > 0 else "<span></span>"
        next_l = f'<a class="next" href="{FLAT[idx+1]}.html"><small>Next</small>{TITLES[FLAT[idx+1]]}</a>' if idx < len(FLAT) - 1 else "<span></span>"
        page = TEMPLATE.format(
            title=meta.get("title", TITLES[slug]),
            desc=html.escape(re.sub(r"<[^>]+>|`", "", meta.get("lead", ""))[:300], quote=True),
            kicker=meta.get("kicker", ""),
            lead=markdown.markdown(meta.get("lead", "")).removeprefix("<p>").removesuffix("</p>"),
            toc=toc, body=body, slug=slug, logo=LOGO, nav=nav_html(slug),
            pager=f'<nav class="pager">{prev_l}{next_l}</nav>',
        )
        (OUT / f"{slug}.html").write_text(page)
    print(f"built {len(FLAT)} pages into {OUT}")


if __name__ == "__main__":
    build()
