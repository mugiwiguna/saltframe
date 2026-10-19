#!/usr/bin/env python3
"""QA for saltframe: home battery + 9-page crawl + link check + interactions."""
import json, sys, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:18766"
PAGES = ["/index.html", "/frames.html", "/material.html", "/process.html",
         "/commissions.html", "/care.html", "/about.html", "/order.html", "/faq.html"]
results = []
def check(name, ok, info=""):
    results.append((name, bool(ok), info))
    print(("PASS" if ok else "FAIL"), "-", name, ("| " + str(info) if info else ""))

errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/home/ubuntu/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome", args=["--no-sandbox"])
    pg = browser.new_page(viewport={"width": 1440, "height": 900})
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(str(e)))

    # ---------- HOME battery ----------
    pg.goto(BASE + "/index.html", wait_until="load")
    pg.wait_for_timeout(700)
    check("hero-art photo", pg.locator(".hero-art img").count() == 1)
    check("no ornament contour", "contour" not in pg.evaluate("getComputedStyle(document.body,'::before').backgroundImage"))
    check("photo natural", pg.evaluate("getComputedStyle(document.querySelector('.hero-art img')).mixBlendMode") == "normal")
    check("headline ink", pg.evaluate("getComputedStyle(document.querySelector('.hero h1')).color") == "rgb(236, 238, 230)")
    check("kicker accent", pg.evaluate("getComputedStyle(document.querySelector('.hero .kicker')).color") == "rgb(215, 230, 0)")
    check("steps 3 col", pg.evaluate("getComputedStyle(document.querySelector('#steps .steps3')).gridTemplateColumns.split(' ').length") == 3)
    check("10YR banner", (pg.locator(".banner").text_content() or "").find("10 YR") >= 0)
    # rail nav
    check("rail nav 9 links", pg.locator(".rail .nav a").count() == 9, pg.locator(".rail .nav a").count())
    check("nav active = home", pg.locator('.rail .nav a[aria-current="page"]').text_content().strip() == "Home")
    # interactions
    pg.locator(".model[data-value='Moss']").click()
    check("frame select", pg.locator("#vFrame").text_content().strip() == "Moss")
    check("drawer opens on card", pg.locator("#detail").evaluate("e=>e.classList.contains('open')"))
    check("drawer data", pg.locator("#dName").text_content().strip() == "Moss" and pg.locator("#dPrice").text_content().strip().endswith("(demo)") and pg.locator("#dSvgG").evaluate("e=>e.children.length") > 0)
    pg.locator("#dUse").click()
    check("drawer closes", not pg.locator("#detail").evaluate("e=>e.classList.contains('open')"))
    pg.locator(".sw[data-value='Tortoise acetate']").click()
    check("material select", pg.locator("#vMaterial").text_content().strip() == "Tortoise acetate")
    pg.locator(".lens[data-value='Sun']").click()
    check("lens select", pg.locator("#vLens").text_content().strip() == "Sun")
    pg.fill("#f-name", "Budi")
    check("engrave live", "BUDI" in pg.locator("#engrave").inner_text())
    # lightbox on hero photo
    pg.locator(".hero-art img").click()
    check("hero lightbox open", pg.locator("#lb").evaluate("e=>e.classList.contains('open')"))
    pg.keyboard.press("Escape")
    check("lb esc close", not pg.locator("#lb").evaluate("e=>e.classList.contains('open')"))
    # heading jump
    before = pg.evaluate("scrollY")
    pg.locator('[data-goto]').first.click(); pg.wait_for_timeout(600)
    check("heading jump", pg.evaluate("scrollY") != before)
    pg.evaluate("scrollTo(0,0)")
    # reveals while scrolling down
    for frac in range(0, 11):
        pg.evaluate(f"scrollTo(0, document.body.scrollHeight*{frac/10})"); pg.wait_for_timeout(120)
    n_show = pg.evaluate("document.querySelectorAll('.rv.show,.rv.on').length")
    n_all = pg.evaluate("document.querySelectorAll('.rv').length")
    check("reveals", n_show == n_all, f"{n_show}/{n_all}")
    imgs = pg.evaluate("[...document.images].filter(i=>i.complete&&i.naturalWidth>0).length")
    total = pg.evaluate("[...document.images].filter(i=>!i.id||i.id!=='lbImg').length")
    check("images loaded", imgs >= total, f"{imgs}/{total}")
    check("parallax", pg.evaluate("getComputedStyle(document.getElementById('matImg')).getPropertyValue('--par')") is not None)
    pg.screenshot(path="qa-full.png", full_page=True)

    # ---------- CRAWL ----------
    hrefs = set()
    for path in PAGES:
        errors.clear()
        resp = pg.goto(BASE + path, wait_until="load")
        pg.wait_for_timeout(350)
        name = path.strip("/")
        check(name + " 200", resp.status == 200, resp.status)
        check(name + " rail nav", pg.locator(".rail .nav a").count() == 9)
        check(name + " active=1", pg.locator('.rail .nav a[aria-current="page"]').count() == 1,
              pg.locator('.rail .nav a[aria-current="page"]').text_content().strip())
        check(name + " footer", pg.locator("footer.footer").count() == 1)
        check(name + " no js error", len(errors) == 0, errors[:2])
        hrefs.update(pg.eval_on_selector_all('a[href^="/"]', "els=>els.map(a=>a.getAttribute('href'))"))
        # reveals
        for frac in range(0, 6):
            pg.evaluate(f"scrollTo(0, document.body.scrollHeight*{frac/5})"); pg.wait_for_timeout(90)
        check(name + " reveals", pg.evaluate("[...document.querySelectorAll('.rv')].every(e=>e.classList.contains('show')||e.classList.contains('on'))"))

    # broken internal links
    bad = []
    for h in sorted(hrefs):
        try:
            r = urllib.request.urlopen(BASE + h.split("?")[0], timeout=5)
            if r.status != 200: bad.append((h, r.status))
        except Exception as e:
            bad.append((h, str(e)))
    check("all internal links 200", not bad, bad)

    # ---------- PAGE-SPECIFIC ----------
    errors.clear()
    pg.goto(BASE + "/frames.html"); pg.wait_for_timeout(400)
    check("frames 3 blocks", pg.locator(".frame").count() == 3)
    check("frames spec", pg.locator(".frame .material-list div").count() >= 18)
    pg.locator(".frame .art img").first.click()
    check("frames lightbox", pg.locator("#lb").evaluate("e=>e.classList.contains('open')"))
    pg.keyboard.press("Escape")

    pg.goto(BASE + "/material.html"); pg.wait_for_timeout(300)
    check("material 3 cards", pg.locator(".pcard").count() == 3)
    check("swatch tortoise", pg.evaluate("getComputedStyle(document.querySelector('.sw-tortoise')).backgroundImage") != "none")
    check("material rows", pg.locator(".material-list div").count() >= 9, pg.locator(".material-list div").count())

    pg.goto(BASE + "/process.html"); pg.wait_for_timeout(300)
    check("timeline 4", pg.locator(".tline .t").count() == 4)

    pg.goto(BASE + "/commissions.html"); pg.wait_for_timeout(400)
    check("gallery 8", pg.locator(".comm").count() == 8)
    pg.locator('.fbtn[data-f="Dune"]').click()
    check("filter Dune = 2", pg.locator(".comm:visible").count() == 2, pg.locator(".comm:visible").count())
    pg.locator('.fbtn[data-f="all"]').click()
    check("filter all = 8", pg.locator(".comm:visible").count() == 8)
    pg.locator(".comm img").first.click()
    check("gallery lightbox", pg.locator("#lb").evaluate("e=>e.classList.contains('open')"))
    pg.keyboard.press("Escape")

    pg.goto(BASE + "/care.html"); pg.wait_for_timeout(300)
    check("care 4 cards", pg.locator(".pcard").count() == 4)
    check("care banner", (pg.locator(".banner").text_content() or "").find("10 YR") >= 0)

    pg.goto(BASE + "/about.html"); pg.wait_for_timeout(300)
    check("about coords", "06" in pg.locator(".coords .val").inner_text())
    check("about bench img", pg.locator(".frame .art img").count() == 1)

    pg.goto(BASE + "/order.html?f=Moss"); pg.wait_for_timeout(300)
    check("order query preselect", pg.locator("#o-frame").input_value() == "Moss")
    check("order engrave default", "SF/03 MOSS" in pg.locator("#engrave").inner_text())
    pg.fill("#o-name", "Sari")
    check("order engrave name", "SARI" in pg.locator("#engrave").inner_text())
    pg.select_option("#o-material", label="Olive acetate")
    check("order summary sync", pg.locator("#sMaterial").text_content().strip() == "Olive acetate")
    check("order selects 3", pg.locator("#oForm select").count() == 3)
    check("no order js error", len(errors) == 0, errors[:2])

    pg.goto(BASE + "/faq.html"); pg.wait_for_timeout(300)
    check("faq 8 items", pg.locator("details.faq").count() == 8)
    pg.locator("details.faq summary").first.click()
    check("faq opens", pg.locator("details.faq").first.get_attribute("open") is not None)
    check("contact 4", pg.locator(".contact .c").count() == 4)

    # ---------- MOBILE (home) ----------
    errors.clear()
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.goto(BASE + "/index.html"); pg.wait_for_timeout(400)
    check("mobile rail top", pg.evaluate("getComputedStyle(document.querySelector('.rail')).position") in ("sticky", "fixed"))
    check("mobile burger visible", pg.locator("#burger").is_visible())
    check("mobile nav hidden", not pg.locator(".nav").is_visible())
    pg.locator("#burger").click(); pg.wait_for_timeout(300)
    check("mobile nav opens", pg.locator(".nav").is_visible())
    pg.locator("#burger").click(); pg.wait_for_timeout(200)
    pg.evaluate("scrollTo(0, document.body.scrollHeight)"); pg.wait_for_timeout(300)
    check("mobile hero cta full", pg.evaluate("document.querySelector('.hero .cta-row .btn').getBoundingClientRect().width") > 300)
    pg.screenshot(path="qa-mobile.png", full_page=True)
    check("mobile no js error", len(errors) == 0, errors[:2])

    browser.close()

passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"\nQA: {passed}/{total} PASS")
sys.exit(0 if passed == total else 1)
