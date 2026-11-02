"""Check lens.html in Edge with Playwright: optics numbers, widths, themes, console, timing.

  python _lens/check_page.py OUTDIR
"""
import json
import math
import os
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8734/lens.html"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
fails = []


def close(name, got, want, tol):
    ok = abs(got - want) <= tol
    print(("ok  " if ok else "FAIL"), name, round(got, 4), "want", want, "+-", tol)
    if not ok:
        fails.append(name)


PROBE = """() => {
  const doc = document.documentElement;
  const wide = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > doc.clientWidth + 1) wide.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right));
  });
  const small = [];
  document.querySelectorAll('a, button, select, input').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    if (el.type === 'checkbox') return;
    if (r.height < 44) small.push(el.tagName + ' ' + (el.textContent || el.id || '').trim().slice(0, 30) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
  });
  const caps = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) {
    if (n.parentElement.closest('script,style')) continue;
    const m = n.textContent.match(/\\b[A-Z]{4,}\\b/g); if (m) caps.push(...m);
  }
  return {scrollW: doc.scrollWidth, clientW: doc.clientWidth, wide: wide.slice(0, 10), small: small.slice(0, 12), caps: [...new Set(caps)]};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")

    # ---------- optics assertions ----------
    ctx = b.new_context(viewport={"width": 1000, "height": 900})
    pg = ctx.new_page()
    errors = []
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "404" not in m.text else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    o = pg.evaluate("() => LensOptics.optics(50, 36, 24, 3, 2.8)")
    close("FF 50 hfov", o["hfov"], 39.598, 0.01)
    close("FF 50 vfov", o["vfov"], 26.991, 0.01)
    close("FF 50 dfov", o["dfov"], 46.793, 0.01)
    close("FF CoC", o["c"], 0.030, 1e-9)
    close("FF 50 f/2.8 3 m near", o["near"], 2.729, 0.002)
    close("FF 50 f/2.8 3 m far", o["far"], 3.330, 0.002)
    close("FF 50 f/2.8 hyperfocal", o["H"], 29.81, 0.01)
    # independent check of near/far: s f^2 / (f^2 +- N c (s - f))
    f, N, c, s = 50.0, 2.8, 0.03, 3000.0
    close("near closed form", o["near"], s * f * f / (f * f + N * c * (s - f)) / 1000, 1e-6)
    close("far closed form", o["far"], s * f * f / (f * f - N * c * (s - f)) / 1000, 1e-6)
    # blur exactly c at the limits
    bn = pg.evaluate("() => LensOptics.blurMM(50, 2.8, 3, LensOptics.optics(50,36,24,3,2.8).near)")
    close("blur at near limit = c", bn, 0.03, 1e-9)
    # Week 9 deck: 36 mm sensor -> 18 sees 90, 35 sees 54, 85 sees 24; Unreal 35 on 23.76 -> 38
    for fl, want in ((18, 90.0), (35, 54.4), (85, 23.9)):
        close(f"Blender {fl} mm hfov", pg.evaluate(f"() => LensOptics.optics({fl}, 36, 20.25, 5, 2.8).hfov"), want, 0.06)
    close("Unreal 35 on 23.76", pg.evaluate("() => LensOptics.optics(35, 23.76, 13.365, 5, 2.8).hfov"), 37.5, 0.06)
    close("APS-C crop", pg.evaluate("() => LensOptics.optics(35, 23.5, 15.6, 5, 2.8).crop"), 43.267 / math.hypot(23.5, 15.6), 1e-3)
    far_inf = pg.evaluate("() => { const o = LensOptics.optics(18, 36, 24, 10, 8); return [o.H, o.far === null || o.far > 1e9]; }")
    print("18 f/8 at 10 m: H", far_inf[0], "far infinite", far_inf[1])
    if not far_inf[1]:
        fails.append("far infinite past H")

    # ---------- UI: set controls, read readouts ----------
    pg.select_option("#sensor", "ff")
    pg.fill("#fNum", "50"); pg.press("#fNum", "Enter")
    pg.fill("#dNum", "3"); pg.press("#dNum", "Enter")
    pg.click('#nPresets button[data-n="2.8"]')
    if not pg.is_checked("#focusFig"):
        pg.check("#focusFig")
    pg.wait_for_timeout(200)
    txt = pg.inner_text("#readouts")
    print("readouts:", txt.replace("\n", " | "))
    for needle in ("39.6°", "27.0°", "46.8°", "2.73 m", "3.33 m", "0.60 m", "29.8 m", "0.030 mm"):
        if needle not in txt:
            fails.append("readout " + needle)
            print("FAIL readout missing", needle)
    # walk mode keeps figure size: 50 -> 85 moves camera 3 -> 5.1
    pg.click('[data-mode="walk"]')
    pg.click('#fPresets button[data-f="85"]')
    pg.wait_for_timeout(100)
    close("walk: distance after 50->85", float(pg.input_value("#dNum")), 5.1, 0.01)
    pg.click('[data-mode="stay"]')
    pg.click('#fPresets button[data-f="24"]')
    close("stay: distance unchanged", float(pg.input_value("#dNum")), 5.1, 0.01)
    # keyboard on the focal slider
    before = float(pg.input_value("#fNum"))
    pg.focus("#fRange"); pg.keyboard.press("ArrowRight"); pg.keyboard.press("ArrowRight")
    after = float(pg.input_value("#fNum"))
    print("keyboard focal", before, "->", after)
    if not after > before:
        fails.append("keyboard focal slider")
    # localStorage
    pg.wait_for_timeout(600)
    saved = pg.evaluate("() => localStorage.getItem('3ddf-lens-v1')")
    print("saved:", saved)
    pg.reload(wait_until="networkidle")
    close("restored focal", float(pg.input_value("#fNum")), after, 0.05)
    # timing of one render at 1000
    t = pg.evaluate("() => { const t0 = performance.now(); for (let i = 0; i < 10; i++) LensRender.render(document.getElementById('view'), {f: 18, sw: 36, sh: 20.25, d: 2, s: 2, N: 1.4}); return (performance.now() - t0) / 10; }")
    print("render ms @1000:", round(t, 1))
    # quiz plays through
    for i in range(8):
        pg.click("#qLens button[data-f='35']")
        pg.click("#qDof button[data-dof='medium']")
        pg.click("#qCheck")
        pg.click("#qNext")
    print("quiz result:", pg.inner_text("#finalScore"), pg.inner_text("#finalNote"))
    best = pg.evaluate("() => JSON.parse(localStorage.getItem('3ddf-lens-v1')).best")
    print("best stored:", best)
    print("console errors:", errors)
    if errors:
        fails.append("console errors")
    ctx.close()

    # ---------- widths, themes, screenshots ----------
    for w in (1000, 390):
        for scheme in ("light", "dark"):
            mobile = w < 500
            ctx = b.new_context(viewport={"width": w, "height": 844 if mobile else 900},
                                device_scale_factor=3 if mobile else 1, color_scheme=scheme,
                                is_mobile=mobile, has_touch=mobile)
            pg = ctx.new_page()
            errs = []
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(URL, wait_until="networkidle")
            pg.wait_for_timeout(300)
            res = pg.evaluate(PROBE)
            print(w, scheme, json.dumps(res), "errors", errs)
            if res["scrollW"] > res["clientW"]:
                fails.append(f"hscroll {w} {scheme}")
            if errs:
                fails.append(f"errors {w} {scheme}")
            if mobile:
                t = pg.evaluate("""() => { const v = document.getElementById('view'); const t0 = performance.now();
                  for (let i = 0; i < 10; i++) LensRender.render(v, {f: 18 + i * 10, sw: 36, sh: 20.25, d: 2 + i, s: 2 + i, N: 1.4}); return (performance.now() - t0) / 10; }""")
                print("render ms @390 dpr3 (capped 2):", round(t, 1))
                pg.evaluate("() => document.getElementById('dolly').click()")
                frames = pg.evaluate("""() => new Promise(r => { let n = 0; const t0 = performance.now();
                  const f = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(f); else r(n / 2); }; requestAnimationFrame(f); })""")
                print("dolly fps @390:", frames)
                pg.wait_for_timeout(2600)
            pg.screenshot(path=os.path.join(OUT, f"lens_{w}_{scheme}.png"), full_page=True)
            if scheme == "light":
                pg.click('[data-cmp="spot"]')
                pg.locator("#compare").screenshot(path=os.path.join(OUT, f"lens_{w}_compare_spot.png"))
                pg.click('[data-cmp="size"]')
                pg.locator("#compare").screenshot(path=os.path.join(OUT, f"lens_{w}_compare_size.png"))
                pg.select_option("#sensor", "blender")
                pg.click('#fPresets button[data-f="85"]')
                pg.click('#nPresets button[data-n="1.4"]')
                pg.wait_for_timeout(200)
                pg.locator("#camera").screenshot(path=os.path.join(OUT, f"lens_{w}_camera_85_f14.png"))
                pg.click("#qLens button[data-f='50']"); pg.click("#qDof button[data-dof='deep']"); pg.click("#qCheck")
                pg.locator("#quiz").screenshot(path=os.path.join(OUT, f"lens_{w}_quiz.png"))
            ctx.close()
    b.close()

print("FAILS:", fails if fails else "none")
