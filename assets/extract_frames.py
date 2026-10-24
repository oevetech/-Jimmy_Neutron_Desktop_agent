"""Recorta automaticamente cada figura de uma folha de sprites com fundo transparente.

Uso:
    python extract_frames.py                 -> processa todas as folhas do anim_config.json
    python extract_frames.py folha.png       -> só detecta e gera a imagem de conferência

As figuras são encontradas pelos espaços vazios (transparentes) entre linhas e colunas,
numeradas em ordem de leitura (esquerda->direita, cima->baixo) e salvas em
C:\\Jimmy\\anim\\<animação>\\00.png, 01.png ... todas do mesmo tamanho, para a escala
não mudar entre um quadro e outro.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
ANIM_DIR = os.path.join(BASE, "anim")
CONFIG = os.path.join(BASE, "anim_config.json")
ALPHA_MIN = 40


def runs(profile, min_gap, min_size):
    """Trechos não vazios de um perfil, juntando buracos pequenos e descartando sujeira."""
    idx = np.flatnonzero(profile)
    if idx.size == 0:
        return []
    out = [[idx[0], idx[0]]]
    for i in idx[1:]:
        if i - out[-1][1] <= min_gap:
            out[-1][1] = i
        else:
            out.append([i, i])
    # Pedaços pequenos (faíscas, parafusos soltos) se juntam ao vizinho mais próximo
    merged = True
    while merged and len(out) > 1:
        merged = False
        for k, (a, b) in enumerate(out):
            if b - a + 1 < min_size:
                left = a - out[k - 1][1] if k > 0 else 1e9
                right = out[k + 1][0] - b if k + 1 < len(out) else 1e9
                if left <= right:
                    out[k - 1][1] = b
                else:
                    out[k + 1][0] = a
                out.pop(k)
                merged = True
                break
    return [(a, b + 1) for a, b in out]


def label(mask):
    """Rotula as manchas conectadas (8 vizinhos).
    Retorna (mapa de rótulos, lista de [área, x0, y0, x1, y1, ids])."""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    labels = np.full(mask.shape, -1, dtype=np.int32)
    comps = []
    for sy, sx in zip(*np.nonzero(mask)):
        if seen[sy, sx]: continue
        cid = len(comps)
        seen[sy, sx] = True
        stack = [(sy, sx)]
        area, x0, y0, x1, y1 = 0, sx, sy, sx, sy
        while stack:
            y, x = stack.pop()
            labels[y, x] = cid
            area += 1
            if x < x0: x0 = x
            if x > x1: x1 = x
            if y < y0: y0 = y
            if y > y1: y1 = y
            for ny in (y - 1, y, y + 1):
                if ny < 0 or ny >= h: continue
                for nx in (x - 1, x, x + 1):
                    if 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        comps.append([area, x0, y0, x1 + 1, y1 + 1, [cid]])
    return labels, comps


def box_gap(a, b):
    dx = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    dy = max(0, max(a[2], b[2]) - min(a[4], b[4]))
    return max(dx, dy)


def remove_white_bg(img):
    """Folha sem transparência (JPG): apaga o fundo branco que encosta na borda e os
    bolsões brancos grandes (vão entre braço e corpo). O branco dos olhos fica."""
    rgb = np.array(img.convert("RGB")).astype(np.int16)
    light = rgb.min(axis=2) >= 232
    labels, comps = label(light)
    h, w = light.shape
    bg = np.zeros_like(light)
    for area, x0, y0, x1, y1, ids in comps:
        touches = x0 == 0 or y0 == 0 or x1 == w or y1 == h
        if touches or area > 400:
            bg |= labels == ids[0]
    # Borda suave: pixels claros colados no fundo ficam semitransparentes
    near = bg.copy()
    near[1:] |= bg[:-1]; near[:-1] |= bg[1:]; near[:, 1:] |= bg[:, :-1]; near[:, :-1] |= bg[:, 1:]
    lum = rgb.mean(axis=2)
    alpha = np.full(light.shape, 255, dtype=np.uint8)
    edge = near & ~bg
    alpha[edge] = np.clip((255 - lum[edge]) * 255 / 60, 0, 255).astype(np.uint8)
    alpha[bg] = 0
    out = np.dstack([rgb.astype(np.uint8), alpha])
    return Image.fromarray(out, "RGBA")


def detect_grade(img, full, grade):
    """Folha com figuras encostadas: corta em grade (faixas de linha, colunas iguais) e,
    em cada célula, fica só com a figura principal (pedaços grandes; sobras dos vizinhos saem)."""
    h, w = full.shape
    cells = []
    for r, (y0, y1, n) in enumerate(grade):
        # Divisões das colunas: perto do ponto esperado, a coluna com menos tinta (o vão entre figuras)
        prof = full[y0:y1].sum(0).astype(float)
        prof = np.convolve(prof, np.ones(9) / 9, mode="same")
        cortes = [0]
        for c in range(1, n):
            alvo, folga = int(w * c / n), int(w / n * 0.35)
            a, b = max(cortes[-1] + 10, alvo - folga), min(w - 10, alvo + folga)
            cortes.append(a + int(np.argmin(prof[a:b])))
        cortes.append(w)
        for c in range(n):
            x0, x1 = cortes[c], cortes[c + 1]
            sub = full[y0:y1, x0:x1]
            labels, comps = label(sub)
            if not comps: continue
            maior = max(cp[0] for cp in comps)
            ids = [cp[5][0] for cp in comps if cp[0] >= maior * 0.15]
            own_sub = np.isin(labels, ids)
            for _ in range(2):
                g = own_sub.copy()
                g[1:] |= own_sub[:-1]; g[:-1] |= own_sub[1:]; g[:, 1:] |= own_sub[:, :-1]; g[:, :-1] |= own_sub[:, 1:]
                own_sub = g
            own = np.zeros_like(full)
            own[y0:y1, x0:x1] = own_sub
            ys, xs = np.nonzero(own_sub & sub)
            cells.append({"row": r, "col": c, "mask": own,
                          "box": (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)})
    return img, cells


def detect(sheet_path, sem_baloes=False, grade=None):
    img = Image.open(sheet_path).convert("RGBA")
    # Sem nenhum pixel transparente (ex.: JPG) -> apaga o fundo branco
    if np.array(img)[:, :, 3].min() == 255:
        img = remove_white_bg(img)
    full = np.array(img)[:, :, 3] >= ALPHA_MIN
    if grade:
        return detect_grade(img, full, grade)
    # Trabalha numa versão reduzida (mais rápido); a escala volta no fim
    k = 2 if max(full.shape) > 900 else 1
    mask = full[::k, ::k]
    labels, comps = label(mask)
    if sem_baloes:
        # Balão de fala vazio = mancha quase toda branca (só o contorno é escuro): descarta
        rgb_small = np.array(img)[::k, ::k, :3].astype(np.int16)
        brancos = []
        for c in comps:
            px = rgb_small[np.isin(labels, c[5])].min(axis=1)
            if c[0] > 50 and px.mean() > 200:
                brancos.append(c)
        # Balão vazado (o miolo branco já virou transparente): contorno fino e oco,
        # pouca tinta para o tamanho da caixa. Leva junto o texto que estiver dentro.
        aneis = []
        for c in comps:
            w, h = c[3] - c[1], c[4] - c[2]
            if c[0] > 60 and w > 20 and h > 12 and c[0] / float(w * h) < 0.2 and w < mask.shape[1] * 0.3:
                aneis.append(c)
        for a in aneis:
            for c in comps:
                if c is not a and c[0] < a[0] and c[1] >= a[1] and c[3] <= a[3] and c[2] >= a[2] and c[4] <= a[4]:
                    brancos.append(c)
        brancos += aneis
        comps = [c for c in comps if not any(c is b for b in brancos)]
    big_area = max(c[0] for c in comps)
    # Manchas grandes são figuras; as pequenas (faíscas, parafusos, fumaça) vão para a figura mais perto
    figs = [c for c in comps if c[0] >= big_area * 0.08]
    for c in comps:
        if c in figs: continue
        near = min(figs, key=lambda f: box_gap(f, c))
        if box_gap(near, c) > mask.shape[0] * 0.12: continue  # sujeira longe de tudo
        near[0] += c[0]
        near[1], near[2] = min(near[1], c[1]), min(near[2], c[2])
        near[3], near[4] = max(near[3], c[3]), max(near[4], c[4])
        near[5] += c[5]
    # "Figura" muito menor que as outras (ex.: lâmpada solta ao lado do Jimmy) é enfeite da vizinha
    if len(figs) >= 3:
        areas = sorted(f[0] for f in figs)
        med_area = areas[len(areas) // 2]
        for f in [f for f in figs if f[0] < med_area * 0.25]:
            others = [o for o in figs if o is not f]
            near = min(others, key=lambda o: box_gap(o, f))
            near[0] += f[0]
            near[1], near[2] = min(near[1], f[1]), min(near[2], f[2])
            near[3], near[4] = max(near[3], f[3]), max(near[4], f[4])
            near[5] += f[5]
            figs.remove(f)
    # Figuras encostadas uma em cima da outra viram uma só, com o dobro da altura:
    # separa no ponto mais vazio do meio
    hs = sorted(f[4] - f[2] for f in figs)
    med = hs[len(hs) // 2]
    split = []
    for f in figs:
        h = f[4] - f[2]
        if h <= 1.6 * med:
            split.append(f + [None])
            continue
        rows_cnt = np.isin(labels[f[2]:f[4], f[1]:f[3]], f[5]).sum(1)
        lo, hi = int(h * 0.3), int(h * 0.7)
        cut = f[2] + lo + int(np.argmin(rows_cnt[lo:hi]))
        for a, b in ((f[2], cut), (cut, f[4])):
            sub = np.isin(labels[a:b, f[1]:f[3]], f[5])
            ys, xs = np.nonzero(sub)
            if len(ys):
                split.append([int(sub.sum()), f[1] + xs.min(), a + ys.min(), f[1] + xs.max() + 1, a + ys.max() + 1,
                              f[5], (a, b)])
    figs = split
    # Ordem de leitura: agrupa em linhas pelo centro vertical, depois esquerda->direita
    figs.sort(key=lambda f: (f[2] + f[4]) / 2)
    rows = []
    for f in figs:
        cy = (f[2] + f[4]) / 2
        if rows and abs(cy - rows[-1][0]) < (f[4] - f[2]) * 0.5:
            rows[-1][1].append(f)
        else:
            rows.append([cy, [f]])
    cells = []
    for r, (_, members) in enumerate(rows):
        for c, f in enumerate(sorted(members, key=lambda f: f[1])):
            box = (f[1] * k, f[2] * k, min(f[3] * k, full.shape[1]), min(f[4] * k, full.shape[0]))
            # Máscara só com os pixels desta figura (folga de 2px p/ manter a borda suavizada)
            own = np.isin(labels, f[5])
            if f[6]:  # parte de uma figura que foi separada
                own[:f[6][0]] = False
                own[f[6][1]:] = False
            for _ in range(2):
                grown = own.copy()
                grown[1:] |= own[:-1]; grown[:-1] |= own[1:]
                grown[:, 1:] |= own[:, :-1]; grown[:, :-1] |= own[:, 1:]
                own = grown
            own = np.repeat(np.repeat(own, k, 0), k, 1)[:full.shape[0], :full.shape[1]]
            cells.append({"row": r, "col": c, "box": box, "mask": own})
    return img, cells


def contact_sheet(img, cells, out_path):
    prev = Image.new("RGBA", img.size, (255, 255, 255, 255))
    prev.alpha_composite(img)
    d = ImageDraw.Draw(prev)
    for i, c in enumerate(cells):
        d.rectangle(c["box"], outline=(255, 0, 0, 255), width=3)
        d.text((c["box"][0] + 4, c["box"][1] + 2), str(i), fill=(0, 0, 255, 255), font_size=28)
    prev.save(out_path)


def tirar_balao(crop):
    """Apaga um balão de fala grudado na figura: miolo branco grande + contorno + pedaços soltos."""
    a = np.array(crop).copy()
    branco = (a[..., 3] > 0) & (a[..., :3].min(axis=2) > 235)
    lab, comps = label(branco)
    apagar = np.zeros(branco.shape, bool)
    for c in comps:
        if c[0] > 300:   # olhos e brilhos são bem menores
            apagar |= np.isin(lab, c[5])
    if not apagar.any():
        return crop
    for _ in range(5):   # cresce 5 px para levar o contorno junto
        g = apagar.copy()
        g[1:] |= apagar[:-1]; g[:-1] |= apagar[1:]; g[:, 1:] |= apagar[:, :-1]; g[:, :-1] |= apagar[:, 1:]
        apagar = g
    a[apagar, 3] = 0
    # Sobras soltas (ponta do balão) longe do corpo
    lab2, comps2 = label(a[..., 3] >= ALPHA_MIN)
    if comps2:
        maior = max(c[0] for c in comps2)
        for c in comps2:
            if c[0] < maior * 0.03:
                a[np.isin(lab2, c[5]), 3] = 0
    out = Image.fromarray(a)
    return out.crop(out.getchannel("A").point(lambda v: 255 if v >= ALPHA_MIN else 0).getbbox())


def crops_of(path, sem_baloes=False, grade=None):
    img, cells = detect(path, sem_baloes, grade)
    rgba = np.array(img)
    crops = []
    for c in cells:
        only = rgba.copy()
        only[~c["mask"], 3] = 0
        crop = Image.fromarray(only).crop(c["box"])
        crops.append(tirar_balao(crop) if sem_baloes else crop)
    return cells, crops


def diag(im):
    return float(np.hypot(im.width, im.height))


def external_frame(entry, crops):
    """Quadro avulso (ex.: um quadro corrigido salvo em arquivo separado), redimensionado
    para o tamanho médio dos quadros indicados em "match"."""
    _, ext = crops_of(os.path.join(BASE, entry["file"]))
    crop = max(ext, key=lambda c: c.width * c.height)
    ref = sum(diag(crops[i]) for i in entry["match"]) / len(entry["match"])
    f = ref / diag(crop)
    return crop.resize((max(1, round(crop.width * f)), max(1, round(crop.height * f))), Image.LANCZOS)


def tirar_buracos(crop, y0, y1, boca=None):
    """Fundo branco preso dentro do desenho (entre o braço e o corpo, entre as pernas):
    apaga as manchas brancas cujo centro fica na faixa de altura [y0, y1] da figura
    (fora dela ficam os olhos, dentes e tênis, que também são brancos).
    boca = [y_max, x_min, x_max]: manchas acima de y_max com x nessa faixa são dentes e ficam."""
    a = np.array(crop)
    al = a[:, :, 3] > 0
    ys = np.nonzero(al.any(axis=1))[0]
    if not len(ys): return crop
    top, alt = ys[0], max(1, ys[-1] - ys[0])
    xs = np.nonzero(al.any(axis=0))[0]
    esq, larg = xs[0], max(1, xs[-1] - xs[0])
    branco = al & (a[:, :, :3].min(axis=2) > 235)
    lab, comps = label(branco)
    apagar = np.zeros(branco.shape, bool)
    for c in comps:
        cy, cx = ((c[2] + c[4]) / 2 - top) / alt, ((c[1] + c[3]) / 2 - esq) / larg
        if boca and cy < boca[0] and boca[1] <= cx <= boca[2]: continue
        if c[0] >= 8 and y0 <= cy <= y1:
            apagar |= np.isin(lab, c[5])
    if not apagar.any(): return crop
    # Leva junto a borda clarinha (antisserrilhado) em volta da mancha
    for _ in range(2):
        g = apagar.copy()
        g[1:] |= apagar[:-1]; g[:-1] |= apagar[1:]; g[:, 1:] |= apagar[:, :-1]; g[:, :-1] |= apagar[:, 1:]
        apagar = g & al & (a[:, :, :3].min(axis=2) > 195)
    a[apagar, 3] = 0
    return Image.fromarray(a)


def export(sheet_name, spec):
    cells, crops = crops_of(os.path.join(BASE, sheet_name), spec.get("sem_baloes", False), spec.get("grade"))
    # Mesmo tamanho de tela para todos os quadros da folha (mantém a proporção entre eles)
    base = crops
    if spec.get("lado_usados"):
        # Só as figuras usadas definem o quadro (uma figura enorme não usada não encolhe as outras)
        usados = {(i["i"] if isinstance(i, dict) else i) for info in spec["animations"].values() for i in info["frames"]
                  if isinstance(i, int) or (isinstance(i, dict) and "i" in i)}
        base = [crops[i] for i in sorted(usados)]
    cw = max(c.width for c in base)
    ch = max(c.height for c in base)
    side = max(cw, ch) + 8
    # "fill": quanto da altura do quadro a figura ocupa (iguala o tamanho entre folhas diferentes)
    if "fill" in spec:
        side = max(int(round(ch / spec["fill"])), cw + 8)
    total = 0
    for anim, info in spec["animations"].items():
        anchor = info.get("anchor", "bottom")
        folder = os.path.join(ANIM_DIR, anim)
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            if f.endswith(".png"): os.remove(os.path.join(folder, f))
        # Tamanho da janela do pet para esta animação (em pixels, com ESCALA = 1)
        with open(os.path.join(folder, "meta.json"), "w", encoding="utf-8") as mf:
            json.dump({"box": info.get("box", spec.get("box", 150))}, mf)
        for n, i in enumerate(info["frames"]):
            if isinstance(i, dict) and "i" in i:
                # Quadro da folha com retângulos para apagar (sobra encostada que não sai sozinha)
                crop = crops[i["i"]].copy()
                for x0, y0, x1, y1 in i.get("apagar", []):
                    crop.paste((0, 0, 0, 0), (x0, y0, x1, y1))
                # Só o branco dentro do retângulo (ex.: fundo preso entre o braço e o pescoço)
                for x0, y0, x1, y1 in i.get("limpar_branco", []):
                    a = np.array(crop)
                    reg = a[y0:y1, x0:x1]
                    reg[reg[:, :, :3].min(axis=2) > 200, 3] = 0
                    crop = Image.fromarray(a)
                crop = crop.crop(crop.getbbox())
            else:
                crop = external_frame(i, crops) if isinstance(i, dict) else crops[i]
            if "buracos" in spec:
                crop = tirar_buracos(crop, *spec["buracos"], boca=spec.get("boca"))
            canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            x = (side - crop.width) // 2
            y = side - crop.height - 4 if anchor == "bottom" else (side - crop.height) // 2
            canvas.alpha_composite(crop, (x, y))
            canvas.save(os.path.join(folder, f"{n:02d}.png"))
            total += 1
    print(f"{sheet_name}: {len(cells)} figuras encontradas, {total} quadros salvos")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        img, cells = detect(path, "--sem-baloes" in sys.argv)
        out = os.path.splitext(path)[0] + "_conferencia.png"
        contact_sheet(img, cells, out)
        rows = {}
        for c in cells: rows[c["row"]] = rows.get(c["row"], 0) + 1
        print(f"{len(cells)} figuras; por linha: {rows}; conferência em {out}")
    else:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
        for sheet, spec in cfg.items():
            export(sheet, spec)
