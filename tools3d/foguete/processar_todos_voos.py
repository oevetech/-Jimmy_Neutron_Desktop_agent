import os
import shutil
import zipfile
import json
from PIL import Image

PROJECT_ROOT = r"C:\Users\everaldolima\jimmy-neutron-pet"
RAW_BASE_DIR = os.path.join(PROJECT_ROOT, "tools3d", "foguete", "raw_voo")
STAGING_DIR = os.path.join(PROJECT_ROOT, "scratch", "staging_pacote_3d")
DIST_ZIP = os.path.join(PROJECT_ROOT, "dist", "pacote_3d.zip")
ASSETS_ZIP = os.path.join(PROJECT_ROOT, "assets", "pacote_3d.zip")
APPDATA_3D = os.path.join(os.environ.get("APPDATA", ""), "JimmyNeutronPet", "anim_3d")

ANIMS = ["voo_pendura", "voo_escala", "voo_senta", "voo_monta"]

# Parâmetros de enquadramento idênticos ao rocket_parked para alinhamento perfeito
REF_BBOX = (129, 50, 704, 407)
REF_W = REF_BBOX[2] - REF_BBOX[0]  # 575
REF_H = REF_BBOX[3] - REF_BBOX[1]  # 357

TARGET_W = 297
scale = TARGET_W / REF_W
TARGET_H = int(round(REF_H * scale))  # 184

CANVAS_SIZE = (305, 305)
GROUND_Y = 301
PASTE_X = 4
BASE_PASTE_Y = GROUND_Y - TARGET_H  # 117

print(f"Alinhamento global: BBOX={REF_BBOX} -> {TARGET_W}x{TARGET_H}")
print(f"Canvas {CANVAS_SIZE}: Paste em ({PASTE_X}, {BASE_PASTE_Y}) apoiado no chão Y={GROUND_Y}")

for anim in ANIMS:
    raw_dir = os.path.join(RAW_BASE_DIR, anim)
    stage_dir = os.path.join(STAGING_DIR, anim)
    app_dir = os.path.join(APPDATA_3D, anim)
    os.makedirs(stage_dir, exist_ok=True)
    os.makedirs(app_dir, exist_ok=True)

    raw_files = sorted(f for f in os.listdir(raw_dir) if f.startswith("raw_") and f.endswith(".png"))
    print(f"\nProcessando '{anim}' ({len(raw_files)} quadros)...")

    for idx, fname in enumerate(raw_files):
        im = Image.open(os.path.join(raw_dir, fname))
        crop = im.crop(REF_BBOX)
        resized = crop.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        canvas.paste(resized, (PASTE_X, BASE_PASTE_Y), resized)

        # Quantização de 256 cores cel-shaded com alfa
        opt = canvas.quantize(colors=256, method=Image.Quantize.FASTOCTREE)

        out_name = f"{idx:02d}.png"
        p_stage = os.path.join(stage_dir, out_name)
        p_app = os.path.join(app_dir, out_name)

        opt.save(p_stage, optimize=True)
        opt.save(p_app, optimize=True)

    # Cria meta.json idêntico para manter escala 159
    meta_content = {"box": 159}
    for folder in [stage_dir, app_dir]:
        with open(os.path.join(folder, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta_content, f)

    print(f"Salvos {len(raw_files)} quadros e meta.json em {anim}")

# Repacota pacote_3d.zip completo
print("\nGerando pacote_3d.zip atualizado...")
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

print("\nProcessamento e empacotamento concluídos com sucesso!")
print(f"Dist ZIP: {DIST_ZIP} ({os.path.getsize(DIST_ZIP)//1024} KB)")
print(f"Assets ZIP: {ASSETS_ZIP} ({os.path.getsize(ASSETS_ZIP)//1024} KB)")
