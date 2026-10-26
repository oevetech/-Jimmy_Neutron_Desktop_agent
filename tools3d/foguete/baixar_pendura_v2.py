"""Baixa do Mixamo (perfil já logado do Playwright) animações de pendurar/escalar para o voo 3D."""
import time, os
from playwright.sync_api import sync_playwright

profile_dir = r"C:\Users\everaldolima\AppData\Local\Temp\chrome_mixamo_profile"
out_dir = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\fbx"
shots = r"C:\Users\everaldolima\jimmy-neutron-pet\tools3d\foguete"

ANIMS = [
    ("hanging idle", "hanging idle", "jimmy_hang_idle.fbx"),
    ("braced hang", "braced hang", "jimmy_braced_hang.fbx"),
    ("hanging", "hanging", "jimmy_hanging.fbx"),
    ("climbing up wall", "climbing up wall", "jimmy_climb_wall.fbx"),
]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=profile_dir, channel="chrome", headless=True, accept_downloads=True,
        args=["--disable-blink-features=AutomationControlled", "--enable-webgl", "--no-sandbox"],
        viewport={"width": 1400, "height": 900})
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.mixamo.com/#/", wait_until="networkidle", timeout=60000)
    time.sleep(4)
    page.screenshot(path=os.path.join(shots, "mixamo_inicio.png"))
    for query, match, fname in ANIMS:
        alvo = os.path.join(out_dir, fname)
        if os.path.exists(alvo) and os.path.getsize(alvo) > 500000:
            print("PULANDO", fname); continue
        print("\nBUSCA", query)
        page.goto(f"https://www.mixamo.com/#/?page=1&query={query}&type=Motion%2CMotionPack",
                  wait_until="networkidle", timeout=60000)
        time.sleep(4)
        try:
            page.wait_for_selector("img[src*='thumbnails/motions/']", timeout=20000)
            cands = []
            for th in page.query_selector_all("img[src*='thumbnails/motions/']"):
                box = th.evaluate_handle("n => n.closest('.product, .item, [ng-repeat]') || n.parentElement.parentElement")
                txt = box.evaluate("n => n.innerText").lower()
                nome = txt.splitlines()[0].strip() if txt.strip() else ""
                cands.append((100 if nome == match else 50 if match in nome else 1, nome, th))
            print("  achados:", [c[1] for c in cands][:12])
            cands.sort(key=lambda c: -c[0])
            if cands[0][0] < 50:
                print("  SEM CORRESPONDENCIA para", match); continue
            print("  escolhido:", cands[0][1])
            cands[0][2].click(force=True)
            time.sleep(7)
            page.wait_for_selector("button:has-text('DOWNLOAD')", timeout=20000).click(force=True)
            time.sleep(3)
            modal = page.wait_for_selector(".modal button:has-text('DOWNLOAD'), [role='dialog'] button:has-text('DOWNLOAD')", timeout=20000)
            with page.expect_download(timeout=120000) as dl:
                modal.click(force=True)
            dl.value.save_as(alvo)
            print("  OK", fname, os.path.getsize(alvo) // 1024, "KB")
            time.sleep(3)
        except Exception as e:
            print("  ERRO", query, e)
            page.screenshot(path=os.path.join(shots, f"erro_{fname}.png"))
    ctx.close()
print("FIM")
