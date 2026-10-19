from playwright.sync_api import sync_playwright
import json, re

CHROME = "/home/ubuntu/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome"
out = {}

def outline(pg):
    return pg.evaluate("""() => {
      const info = [];
      document.querySelectorAll('header,section,footer,nav,main > div,main > *').forEach(el => {
        const r = el.getBoundingClientRect();
        info.push({tag: el.tagName.toLowerCase(), cls: (el.className||'').toString().slice(0,60),
                   h: Math.round(r.height), text: (el.innerText||'').replace(/\\s+/g,' ').slice(0,180)});
      });
      const cs = getComputedStyle(document.body);
      const h1 = document.querySelector('h1,h2');
      return {sections: info, bg: cs.backgroundColor, color: cs.color, font: cs.fontFamily,
              h1size: h1 ? getComputedStyle(h1).fontSize : null,
              h1font: h1 ? getComputedStyle(h1).fontFamily : null,
              height: document.body.scrollHeight};
    }""")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    for name, url in [("ref", "https://krakenindustries.co/"), ("mine", "http://43.133.150.249:18766/index.html")]:
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        try:
            pg.goto(url, wait_until="networkidle", timeout=45000)
        except Exception:
            pass
        pg.wait_for_timeout(2000)
        pg.evaluate("""async () => { for (let y=0; y<=document.body.scrollHeight; y+=innerHeight*0.7){ window.scrollTo({top:y}); await new Promise(r=>setTimeout(r,150)); } window.scrollTo({top:0}); }""")
        pg.wait_for_timeout(1200)
        out[name] = outline(pg)
        pg.screenshot(path=f"/home/ubuntu/saltframe/qa-cmp-{name}.png", full_page=True)
        pg.close()
    b.close()

print(json.dumps(out, indent=1))
