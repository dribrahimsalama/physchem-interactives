---
name: physchem-interactive
description: Build, edit or review an interactive activity in the physchem-interactives repo (static HTML/CSS/JS physical chemistry teaching tools for Moodle). Use when adding a new activity, changing an existing one, or adding it to the catalogue and README.
---

# physchem-interactive

The site is plain static HTML/CSS/JS: no frameworks, build step, backend, login, analytics or database. It is hosted on GitHub Pages and embedded in Moodle.

## Repo conventions

- One folder per activity: `<topic>/<slug>/index.html`. Topics: gases, thermodynamics, kinetics, equilibria, electrochemistry.
- `index.html` at the root is the catalogue. Each activity is an `<li class="activity-card">` (h3, one-sentence p, `a.button-link`) inside its topic's `<section>`. Use HTML entities (`&ndash;`, `&Delta;`).
- `README.md` has a Structure tree listing every activity. Update both when adding one.
- Each activity page is a thin wrapper (CSP meta plus a sandboxed `<iframe srcdoc="…">`) around an escaped inner document. The inner document uses the `--foreground`, `--card`, `--primary`, `--border`, `--viz-series-1..6` CSS variables, so light and dark mode work. D3 v7.9.0 is loaded from cdn.jsdelivr.net, which the CSP allows. Allowed CDNs: cdnjs, jsdelivr, esm.sh, unpkg, Google/Bunny fonts. Nothing else.
- Case studies (`corrosion-prediction`, `shelf-life-prediction`) are slide-story pages. Concept explorers (`arrhenius`, `gibbs-energy`) are controls + chart + interpretation panel.

## Workflow for a new activity

1. Copy the closest existing page to `<topic>/<new-slug>/index.html` and change the title in both places (outer `<title>` and iframe `title`).
2. Edit the inner document in readable form with the helper:
   ```bash
   python3 .claude/skills/physchem-interactive/scripts/srcdoc.py unwrap <page> /tmp/inner.html
   # edit /tmp/inner.html
   python3 .claude/skills/physchem-interactive/scripts/srcdoc.py wrap <page> /tmp/inner.html
   ```
   Unwrap then wrap with no edits is byte-identical, so diffs stay small.
3. Add the catalogue card and README line.
4. Verify (below), commit, and push to the working branch.

## Quality bar for the content

- Physics first: correct equations, SI units with ⁻¹ superscripts, sensible default values. State assumptions (ideal gas, standard state, constant ΔH).
- Every control shows its live value in an `<output>`. Every chart has `role="img"` and a title and description, plus an `aria-live` text line explaining what the learner is seeing.
- Interpretation text must change with the controls (not static prose). End with a "what to try" prompt or a self-check question.
- Accessible: keyboard operable, labels on all inputs, contrast in both themes, no colour-only encoding (use dashes or labels too).
- Responsive down to ~360 px wide (Moodle embeds are narrow). No horizontal page scroll.
- Distinct and intentional visuals, not a generic template. Match the existing activities' tone.

## Verification (do this before reporting done)

```bash
python3 -m http.server 8000 &
pip install playwright   # once; Python bindings
CHROMIUM_PATH=/opt/pw-browsers/chromium python3 .claude/skills/physchem-interactive/scripts/smoke_test.py \
  --shots /tmp/shots <topic>/<slug>/index.html
```

`smoke_test.py` checks each page at 360 px and 1280 px for console and page errors, horizontal overflow, a rendered chart, and that every slider visibly changes the page. It exits 1 on failure. Then look at the screenshots yourself, since the script can't judge whether a chart is sensible.

If the sandbox blocks cdn.jsdelivr.net (symptom: `d3 is not defined`), fetch D3 through npm and inject it:

```bash
npm pack d3@7.9.0 && tar xzf d3-7.9.0.tgz package/dist/d3.min.js
# add: --d3 package/dist/d3.min.js
```

Also open the root `index.html` and confirm the new card's link resolves.
