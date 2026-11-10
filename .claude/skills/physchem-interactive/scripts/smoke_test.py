#!/usr/bin/env python3
"""Smoke-test activity pages: python3 smoke_test.py [--base URL] [--shots DIR] [--d3 FILE] PAGE...

Env CHROMIUM_PATH=/opt/pw-browsers/chromium uses the pre-installed browser.

PAGE is a path like kinetics/arrhenius/index.html. Serve the repo first
(python3 -m http.server 8000). For each page, at 360 px and 1280 px wide it checks:
no console errors / page errors / failed requests, no horizontal scroll, the chart
(svg/canvas) renders, and that every range slider changes its <output> or the chart.
Exit code 1 if any check fails.
"""
import argparse, os, sys
from playwright.sync_api import sync_playwright

def inner(page):
    for f in page.frames:
        if f != page.main_frame:
            return f
    return page.main_frame

D3 = None

def run(pw, base, path, shots):
    problems = []
    b = pw.chromium.launch(headless=True, **({"executable_path": os.environ["CHROMIUM_PATH"]} if os.environ.get("CHROMIUM_PATH") else {}))
    for w, h in ((360, 800), (1280, 900)):
        ctx = b.new_context(viewport={"width": w, "height": h})
        if D3:  # offline sandbox: inject D3 into every frame before page scripts run
            ctx.add_init_script(path=D3)
        pg = ctx.new_page()
        errs = []
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" and not (D3 and "ERR_TUNNEL_CONNECTION_FAILED" in m.text) else None)
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("requestfailed", lambda r: errs.append("request failed: " + r.url) if not (D3 and "d3.min.js" in r.url) else None)
        pg.goto(f"{base}/{path}"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(500)
        fr = inner(pg)
        if fr.evaluate("document.documentElement.scrollWidth > innerWidth + 1"):
            problems.append(f"{w}px: horizontal overflow")
        if not fr.evaluate("!!document.querySelector('svg *, canvas')"):
            problems.append(f"{w}px: no chart elements rendered")
        if w == 1280:
            for s in fr.query_selector_all("input[type=range]"):
                sid = s.get_attribute("id") or "?"
                before = fr.evaluate("document.body.innerText + document.querySelectorAll('svg').length + [...document.querySelectorAll('svg')].map(s=>s.innerHTML.length).join()")
                lo, hi, cur = (float(s.get_attribute(a) or 0) for a in ("min", "max", "value"))
                target = lo + (hi - lo) * (0.8 if cur < lo + (hi - lo) * 0.5 else 0.2)
                s.evaluate("(e,v)=>{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}", target)
                pg.wait_for_timeout(300)
                after = fr.evaluate("document.body.innerText + document.querySelectorAll('svg').length + [...document.querySelectorAll('svg')].map(s=>s.innerHTML.length).join()")
                if before == after:
                    problems.append(f"slider #{sid}: moving it changed nothing visible")
        if shots:
            os.makedirs(shots, exist_ok=True)
            pg.screenshot(path=os.path.join(shots, path.replace("/", "_") + f".{w}.png"), full_page=True)
        problems += [f"{w}px: {e}" for e in dict.fromkeys(errs)]
        pg.close()
    b.close()
    return problems

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="http://localhost:8000")
ap.add_argument("--shots")
ap.add_argument("--d3", help="local d3.min.js to use when the CDN is unreachable (npm pack d3@7.9.0)")
ap.add_argument("pages", nargs="+")
a = ap.parse_args()
D3 = a.d3
bad = 0
with sync_playwright() as pw:
    for p in a.pages:
        pr = run(pw, a.base, p, a.shots)
        print(("FAIL " if pr else "ok   ") + p)
        for x in pr: print("     - " + x)
        bad += bool(pr)
sys.exit(1 if bad else 0)
