import os
import time
from playwright.sync_api import sync_playwright

profile_dir = r"C:\Users\everaldolima\AppData\Local\Temp\chrome_mixamo_profile"
queries = ["pilot", "steering", "hover", "flying", "fall", "climbing"]

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        channel="chrome",
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--enable-webgl", "--no-sandbox"],
        viewport={"width": 1400, "height": 900}
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://www.mixamo.com/#/", wait_until="networkidle", timeout=45000)
    time.sleep(3)

    for q in queries:
        url = f"https://www.mixamo.com/#/?page=1&query={q}&type=Motion%2CMotionPack"
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(3)
        thumbs = page.query_selector_all("img[src*='thumbnails/motions/']")
        print(f"\nBusca '{q}': {len(thumbs)} resultados encontrados")
        names = []
        for t in thumbs[:8]:
            try:
                container = t.evaluate_handle("el => el.closest('.product') || el.parentElement.parentElement")
                txt = container.evaluate("el => el.innerText").strip()
                first = txt.splitlines()[0] if txt else ""
                names.append(first)
            except Exception:
                pass
        if names:
            print("  Exemplos:", ", ".join(names))
