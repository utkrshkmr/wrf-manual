# WRF-Fire Manual

A hands-on manual for building and running WRF-Fire (WRF 4.6, WPS 4.6) by hand on UB's CCR cluster, plus our lab's record of the setup, the October 2026 scaling campaign, and the workflow designed from it.

- `src/*.md` — page sources (one per page; a header block gives title, kicker and lead)
- `src/diagrams/*.svg` — every diagram and chart, themed for light and dark
- `static/style.css` — the stylesheet
- `tools/build.py` — builds `src/` into `docs/` (needs `pip install markdown`)
- `docs/` — the built site; serve it with GitHub Pages from the `docs/` folder

```bash
python3 tools/build.py
python3 -m http.server -d docs 8000
```
