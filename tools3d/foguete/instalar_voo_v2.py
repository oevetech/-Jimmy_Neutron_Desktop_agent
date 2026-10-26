"""Recorta os quadros de raw_voo_v2/<anim>, grava no anim_3d do pet e troca as animações nos pacote_3d.zip.

python instalar_voo_v2.py voo_pendura,voo_escala,voo_senta,voo_monta [box]
Todas as animações passadas usam o MESMO recorte e escala, para o foguete não pular na troca de fase.
"""
import os, sys, json, zipfile, shutil
from PIL import Image

RAIZ = r"C:\Users\everaldolima\jimmy-neutron-pet"
anims = sys.argv[1].split(",")
box = int(sys.argv[2]) if len(sys.argv) > 2 else 200
LADO = 300  # quadro quadrado, como os do 2D

quadros = {}
for anim in anims:
    raw = os.path.join(RAIZ, "tools3d", "foguete", "raw_voo_v2", anim)
    quadros[anim] = [Image.open(os.path.join(raw, f)).convert("RGBA")
                     for f in sorted(os.listdir(raw)) if f.startswith("raw_")]
# Recorte comum (união do que não é transparente em todos os quadros de todas as fases)
caixas = [f.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox() for fr in quadros.values() for f in fr]
x0, y0 = min(c[0] for c in caixas), min(c[1] for c in caixas)
x1, y1 = max(c[2] for c in caixas), max(c[3] for c in caixas)
esc = (LADO - 4) / max(x1 - x0, y1 - y0)
w, h = round((x1 - x0) * esc), round((y1 - y0) * esc)
meta = json.dumps({"box": box})

novos = {}
for anim, fr in quadros.items():
    destinos = [os.path.join(os.environ["APPDATA"], "JimmyNeutronPet", "anim_3d", anim),
                os.path.join(RAIZ, "scratch", "staging_pacote_3d", anim)]
    for d in destinos:
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for i, f in enumerate(fr):
        q = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
        peca = f.crop((x0, y0, x1, y1)).resize((w, h), Image.Resampling.LANCZOS)
        q.paste(peca, ((LADO - w) // 2, LADO - 2 - h), peca)   # apoiado embaixo
        for d in destinos:
            q.save(os.path.join(d, f"{i:02d}.png"), optimize=True)
    for d in destinos:
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as fh: fh.write(meta)
    novos[anim] = destinos[0]
    print("OK", anim, len(fr), "quadros")

# Troca as animações dentro dos zips (o resto do pacote fica igual)
for z in (os.path.join(RAIZ, "assets", "pacote_3d.zip"), os.path.join(RAIZ, "dist", "pacote_3d.zip")):
    tmp = z + ".tmp"
    with zipfile.ZipFile(z) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            if it.filename.split("/")[0] not in novos:
                zout.writestr(it, zin.read(it.filename))
        for anim, pasta in novos.items():
            for nome in sorted(os.listdir(pasta)):
                zout.write(os.path.join(pasta, nome), f"{anim}/{nome}")
    os.replace(tmp, z)
    print("ZIP", z, os.path.getsize(z) // 1024, "KB")
print("box", box, "conteudo", w, "x", h)
