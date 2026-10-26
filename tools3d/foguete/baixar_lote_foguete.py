import time
import os
import sys
from playwright.sync_api import sync_playwright

profile_dir = r"C:\Users\everaldolima\AppData\Local\Temp\chrome_mixamo_profile"
out_dir = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\fbx"
os.makedirs(out_dir, exist_ok=True)

ANIMS = [
    {"query": "pilot", "match": "piloting", "filename": "jimmy_flight_pilot.fbx", "in_place": False},
    {"query": "flying", "match": "flying", "filename": "jimmy_flight_flying.fbx", "in_place": True},
    {"query": "climbing ladder", "match": "climbing ladder", "filename": "jimmy_flight_climb.fbx", "in_place": True},
    {"query": "pilot flips switches", "match": "pilot flips switches", "filename": "jimmy_flight_switches.fbx", "in_place": False},
]

print("Iniciando Playwright para baixar animações do foguete...")
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        channel="chrome",
        headless=True,
        accept_downloads=True,
        downloads_path=out_dir,
        args=["--disable-blink-features=AutomationControlled", "--enable-webgl", "--no-sandbox"],
        viewport={"width": 1400, "height": 900}
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://www.mixamo.com/#/", wait_until="networkidle", timeout=45000)
    time.sleep(4)

    for item in ANIMS:
        filename = item["filename"]
        target_path = os.path.join(out_dir, filename)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 500000:
            print(f"[PULANDO] {filename} já existe ({os.path.getsize(target_path)//1024} KB).")
            continue

        query = item["query"]
        match_word = item["match"].lower()
        in_place = item["in_place"]

        print(f"\nBuscando: '{query}' para {filename}...")
        url = f"https://www.mixamo.com/#/?page=1&query={query}&type=Motion%2CMotionPack"
        page.goto(url, wait_until="networkidle", timeout=45000)
        time.sleep(4)

        try:
            page.wait_for_selector("img[src*='thumbnails/motions/']", timeout=20000)
            thumbnails = page.query_selector_all("img[src*='thumbnails/motions/']")
            print(f"Encontradas {len(thumbnails)} animações para '{query}'")

            candidates = []
            for thumb in thumbnails:
                container = thumb.evaluate_handle("node => node.closest('.product, .item, [ng-repeat]') || node.parentElement.parentElement")
                txt = container.evaluate("node => node.innerText").lower()
                first_line = txt.splitlines()[0].strip() if txt.splitlines() else ""
                score = 0
                if first_line == match_word:
                    score = 100
                elif match_word in first_line:
                    score = 50
                elif match_word in txt:
                    score = 20
                else:
                    score = 1
                candidates.append((score, first_line, thumb, container))

            candidates.sort(key=lambda c: c[0], reverse=True)
            best = candidates[0]
            print(f"Selecionando: '{best[1]}' (score: {best[0]})")
            best[2].click(force=True)
            time.sleep(6) # Aguarda aplicar a pose ao modelo do Jimmy

            if in_place:
                try:
                    labels = page.query_selector_all("label, span, div")
                    for lbl in labels:
                        t = lbl.inner_text().strip().lower()
                        if t == "in place":
                            print("Marcando 'In Place'...")
                            lbl.click(force=True)
                            time.sleep(2)
                            break
                except Exception as e:
                    print("Aviso ao tentar In Place:", e)

            print("Clicando no botão DOWNLOAD...")
            dl_btn = page.wait_for_selector("button:has-text('DOWNLOAD')", timeout=20000)
            dl_btn.click(force=True)
            time.sleep(3)

            print("Confirmando modal de download...")
            modal_dl = page.wait_for_selector(".modal button:has-text('DOWNLOAD'), [role='dialog'] button:has-text('DOWNLOAD')", timeout=20000)

            with page.expect_download(timeout=90000) as dl_info:
                modal_dl.click(force=True)

            download = dl_info.value
            download.save_as(target_path)
            size = os.path.getsize(target_path)
            print(f"[SUCESSO] Baixado: {filename} ({size//1024} KB)")
            time.sleep(3)

        except Exception as e:
            print(f"[ERRO] Falha ao baixar '{query}': {e}")
            page.screenshot(path=os.path.join(r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete", f"erro_{filename}.png"))

print("\nProcessamento finalizado!")
