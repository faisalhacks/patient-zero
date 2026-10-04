"""Open-check for patient_zero.html (optional; needs playwright + chromium).
Loads the page from disk, fails on console errors or external scripts, exercises the
keyboard tabs and the replay, and confirms the graph and results section rendered."""
import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("check_page: playwright not installed, skipped"); return 0
    page_path = (ROOT / "patient_zero.html").resolve().as_uri()
    errs, reqs = [], []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        pg.on("console", lambda m: errs.append((m.type, m.text)) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(("pageerror", str(e))))
        pg.on("request", lambda r: reqs.append(r.url))
        pg.goto(page_path); pg.wait_for_timeout(800)
        tabs = pg.locator('#sel [role=tab]').count()
        pg.locator('#sel [role=tab]').first.focus(); pg.keyboard.press("ArrowRight"); pg.wait_for_timeout(100)
        sel_after = pg.evaluate("[...document.querySelectorAll('#sel [role=tab]')].findIndex(b=>b.getAttribute('aria-selected')==='true')")
        focused = pg.evaluate("document.activeElement && document.activeElement.id")
        pg.keyboard.press("End"); pg.wait_for_timeout(100)
        sel_end = pg.evaluate("[...document.querySelectorAll('#sel [role=tab]')].findIndex(b=>b.getAttribute('aria-selected')==='true')")
        nodes = pg.locator('#graph circle.node').count(); edges = pg.locator('#graph path.edge').count()
        findings_h3 = pg.locator('#findings h3').count(); badges = pg.locator('#findings .badge').count()
        pg.click('#play'); pg.wait_for_timeout(300); clock = pg.inner_text('#clock')
        verdict = pg.inner_text('#readout .verdict')
        main_count = pg.locator('main').count(); h2s = pg.locator('h2').count()
        b.close()
    ext_js = [u for u in reqs if u.endswith(".js") and u.startswith("http")]
    print(f"tabs={tabs} arrow->{sel_after} focused={focused} end->{sel_end} graph nodes={nodes} edges={edges} "
          f"findings h3={findings_h3} badges={badges} main={main_count} h2={h2s}")
    print("clock during replay:", clock[:80]); print("verdict:", verdict[:140])
    print("external script requests:", ext_js or "none"); print("console errors:", errs or "none")
    ok = (not errs and not ext_js and tabs >= 8 and sel_after == 1 and focused == "tab-1" and sel_end == tabs - 1
          and nodes > 10 and edges > 5 and findings_h3 >= 5 and badges >= 4 and main_count == 1)
    print("PAGE CHECK", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
