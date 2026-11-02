"""Check capture.html in Edge with Playwright: widths, themes, ticks, tap targets.

  python _capture/check_page.py OUTDIR
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8734/capture.html"
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

PROBE = """() => {
  const doc = document.documentElement;
  const small = [];
  document.querySelectorAll('a, button, label, input').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    if (el.tagName === 'INPUT' && el.closest('label')) return;
    if (r.height < 44 || r.width < 44) small.push(el.tagName + ' ' + (el.textContent || '').trim().slice(0, 40) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
  });
  const wide = [];
  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width && r.right > doc.clientWidth + 1) wide.push(el.tagName + '.' + el.className + ' ' + Math.round(r.right));
  });
  const caps = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n; while ((n = walker.nextNode())) {
    const t = n.textContent; const m = t.match(/\b[A-Z]{4,}\b/g);
    if (m) caps.push(...m);
  }
  return {scrollW: doc.scrollWidth, clientW: doc.clientWidth, small: small.slice(0, 30), wide: wide.slice(0, 15), caps: [...new Set(caps)]};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    for w in (390, 360, 1000):
        for scheme in ("light", "dark"):
            ctx = b.new_context(viewport={"width": w, "height": 844 if w < 500 else 900},
                                device_scale_factor=2 if w < 500 else 1, color_scheme=scheme,
                                is_mobile=w < 500, has_touch=w < 500)
            pg = ctx.new_page()
            pg.goto(URL, wait_until="networkidle")
            for mode in ("object", "place"):
                pg.click(f'.modes button[data-mode="{mode}"]')
                pg.evaluate("() => document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
                pg.wait_for_timeout(400)
                res = pg.evaluate(PROBE)
                print(w, scheme, mode, json.dumps(res))
                if scheme == "light" or w == 390:
                    pg.screenshot(path=os.path.join(OUT, f"capture_{w}_{scheme}_{mode}.png"), full_page=True)
            ctx.close()

    # ticks survive a reload, per mode
    ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.goto(URL, wait_until="networkidle")
    pg.click('.modes button[data-mode="object"]')
    labels = pg.locator('ul.ticks li:not(.m-place) label')
    labels.nth(0).tap(); labels.nth(2).tap()
    t1 = pg.inner_text("#tally b")
    pg.click('.modes button[data-mode="place"]')
    pg.locator('ul.ticks li:not(.m-object) label').nth(1).tap()
    t2 = pg.inner_text("#tally b")
    pg.reload(wait_until="networkidle")
    mode_after = pg.get_attribute("body", "data-mode")
    t3 = pg.inner_text("#tally b")
    pg.click('.modes button[data-mode="object"]')
    t4 = pg.inner_text("#tally b")
    checked = pg.evaluate("() => [...document.querySelectorAll('input[data-id]:checked')].map(i => i.dataset.id)")
    print("ticks:", t1, t2, "after reload:", mode_after, t3, "object:", t4, checked)
    pg.screenshot(path=os.path.join(OUT, "capture_390_ticked.png"))
    pg.click("#clear")
    print("after clear:", pg.inner_text("#tally b"))
    b.close()
