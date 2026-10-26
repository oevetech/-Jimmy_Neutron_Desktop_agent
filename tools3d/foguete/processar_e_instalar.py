import os
import shutil
import zipfile
import json
from PIL import Image

PROJECT_ROOT = r"C:\Users\everaldolima\jimmy-neutron-pet"
RAW_DIR = os.path.join(PROJECT_ROOT, "tools3d", "foguete", "raw_frames")
STAGING_DIR = os.path.join(PROJECT_ROOT, "scratch", "staging_pacote_3d")
STAGING_ROCKET = os.path.join(STAGING_DIR, "rocket_parked")
DIST_ZIP = os.path.join(PROJECT_ROOT, "dist", "pacote_3d.zip")
ASSETS_ZIP = os.path.join(PROJECT_ROOT, "assets", "pacote_3d.zip")
APPDATA_3D = os.path.join(os.environ.get("APPDATA", ""), "JimmyNeutronPet", "anim_3d")
APPDATA_ROCKET = os.path.join(APPDATA_3D, "rocket_parked")

os.makedirs(STAGING_ROCKET, exist_ok=True)
os.makedirs(APPDATA_ROCKET, exist_ok=True)

# 1. Determina a caixa de enquadramento global da sequência (baseada no quadro 0)
f0 = Image.open(os.path.join(RAW_DIR, "raw_00.png"))
ref_bbox = f0.getbbox()
ref_w = ref_bbox[2] - ref_bbox[0]
ref_h = ref_bbox[3] - ref_bbox[1]

TARGET_W = 297
scale = TARGET_W / ref_w
TARGET_H = int(round(ref_h * scale))

CANVAS_SIZE = (305, 305)
GROUND_Y = 301
PASTE_X = 4
BASE_PASTE_Y = GROUND_Y - TARGET_H

print(f"Enquadramento: Ref {ref_w}x{ref_h} -> Alvo {TARGET_W}x{TARGET_H}")
print(f"Posicionamento no Canvas 305x305: X={PASTE_X}, Y={BASE_PASTE_Y} até {GROUND_Y}")

# 2. Processa cada quadro
raw_files = sorted(f for f in os.listdir(RAW_DIR) if f.startswith("raw_") and f.endswith(".png"))
print(f"Processando {len(raw_files)} quadros...")

for idx, fname in enumerate(raw_files):
    raw_path = os.path.join(RAW_DIR, fname)
    im = Image.open(raw_path)
    
    # Recorta usando a caixa de referência fixa para preservar a oscilação natural de hover
    crop = im.crop(ref_bbox)
    resized = crop.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    canvas.paste(resized, (PASTE_X, BASE_PASTE_Y), resized)
    
    # Quantização 256 cores toon com transparência
    opt = canvas.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
    
    out_name = f"{idx:02d}.png"
    p_stage = os.path.join(STAGING_ROCKET, out_name)
    p_app = os.path.join(APPDATA_ROCKET, out_name)
    
    opt.save(p_stage, optimize=True)
    opt.save(p_app, optimize=True)

# 3. Cria meta.json
meta_content = {"box": 159}
for folder in [STAGING_ROCKET, APPDATA_ROCKET]:
    with open(os.path.join(folder, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_content, f)

print(f"Salvos {len(raw_files)} quadros e meta.json em:")
print(f" - {STAGING_ROCKET}")
print(f" - {APPDATA_ROCKET}")

# 4. Atualiza os arquivos pacote_3d.zip em dist/ e assets/
print("\nCompactando pacote_3d.zip completo...")
temp_zip = os.path.join(PROJECT_ROOT, "scratch", "pacote_3d_temp.zip")
with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for folder_name in sorted(os.listdir(STAGING_DIR)):
        folder_path = os.path.join(STAGING_DIR, folder_name)
        if os.path.isdir(folder_path):
            for file_name in sorted(os.listdir(folder_path)):
                file_path = os.path.join(folder_path, file_name)
                arcname = f"{folder_name}/{file_name}"
                z.write(file_path, arcname)

shutil.copy2(temp_zip, DIST_ZIP)
shutil.copy2(temp_zip, ASSETS_ZIP)
os.remove(temp_zip)

print("SUCESSO TOTAL!")
print(f"Dist ZIP atualizado: {DIST_ZIP} ({os.path.getsize(DIST_ZIP)//1024} KB)")
print(f"Assets ZIP atualizado: {ASSETS_ZIP} ({os.path.getsize(ASSETS_ZIP)//1024} KB)")
