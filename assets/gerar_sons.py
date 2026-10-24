"""Gera os sons do pet em C:\\Jimmy\\sons (WAV 44.1 kHz, mono, 16 bits).

Uso:  python gerar_sons.py           -> cria só os que ainda não existem
      python gerar_sons.py --todos   -> recria todos (apaga sons trocados por você!)

Para usar um som seu, é só salvar um .wav com o mesmo nome na pasta sons.
"""
import os
import sys
import wave

import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sons")
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def lowpass(x, cutoff):
    """Passa-baixa de 1 polo; cutoff pode variar ao longo do tempo (array)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def sweep(f0, f1, sec, curve=1.0):
    """Senoide com frequência indo de f0 a f1."""
    tt = t(sec)
    f = f0 + (f1 - f0) * (tt / sec) ** curve
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def fade(x, a=0.005, r=0.05):
    n_a, n_r = int(a * SR), int(r * SR)
    env = np.ones(len(x))
    if n_a: env[:n_a] = np.linspace(0, 1, n_a)
    if n_r: env[-n_r:] = np.linspace(1, 0, n_r)
    return x * env


def save(name, x, peak=0.9):
    x = x / (np.max(np.abs(x)) + 1e-9) * peak
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def explosao():
    sec = 2.4
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    # Estrondo: ruído que vai ficando abafado + grave descendo
    body = lowpass(noise, 3000 * np.exp(-tt * 2.2) + 120) * np.exp(-tt * 1.6)
    boom = sweep(70, 28, sec, 0.5) * np.exp(-tt * 2.0) * 1.4
    # Estalos dos destroços
    crackle = np.zeros(len(tt))
    for _ in range(60):
        i = int(rng.uniform(0.05, 1.6) * SR)
        n = int(0.004 * SR)
        crackle[i:i + n] += rng.standard_normal(n) * np.exp(-i / SR * 2) * 0.6
    x = body * 1.2 + boom + lowpass(crackle, 4000)
    return fade(x, 0.002, 0.3)


def decolagem():
    sec = 2.6
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    rumble = lowpass(noise, 250 + 500 * tt / sec)  # ronco ficando mais agudo
    roar = lowpass(noise, 1800) * 0.35
    motor = sweep(55, 140, sec, 1.4) * 0.5
    env = np.minimum(1, tt / 0.6)  # cresce no início
    return fade((rumble * 1.5 + roar + motor) * env, 0.01, 0.6)


def paraquedas():
    sec = 0.7
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    env = np.sin(np.pi * np.minimum(1, tt / sec)) ** 2
    whoosh = lowpass(noise, 600 + 2500 * env) - lowpass(noise, 300)
    pop = sweep(180, 90, sec) * np.exp(-tt * 18) * 0.8
    return fade(whoosh * env * 1.4 + pop, 0.005, 0.1)


def pouso():
    sec = 0.45
    tt = t(sec)
    thud = sweep(110, 45, sec, 0.4) * np.exp(-tt * 11)
    click = lowpass(rng.standard_normal(len(tt)), 1500) * np.exp(-tt * 60) * 0.8
    return fade(thud + click, 0.001, 0.08)


def goddard():
    # Bip-bip robótico (dois tons, onda meio quadrada)
    parts = []
    for f, sec in ((1250, 0.09), (0, 0.05), (1650, 0.12)):
        tt = t(sec)
        if f:
            s = np.tanh(3 * np.sin(2 * np.pi * f * tt)) * (1 + 0.15 * np.sin(2 * np.pi * 30 * tt))
            parts.append(fade(s, 0.004, 0.02))
        else:
            parts.append(np.zeros(len(tt)))
    return np.concatenate(parts) * 0.8


def latido():
    # Latido robótico: dois "au" com o tom caindo, harmônicos e um zumbido metálico
    parts = []
    for f0, f1, sec in ((620, 300, 0.17), (0, 0, 0.17), (560, 260, 0.2)):
        tt = t(sec)
        if not f0:
            parts.append(np.zeros(len(tt)))
            continue
        base = sweep(f0, f1, sec, 0.6)
        voz = np.tanh(2.5 * base) + 0.4 * np.sin(2 * np.arcsin(np.clip(base, -1, 1)) * 2)
        metal = np.sin(2 * np.pi * 95 * tt) * 0.35 + 1
        rasp = lowpass(rng.standard_normal(len(tt)), 2500) * 0.25
        env = np.minimum(1, tt / 0.012) * np.exp(-tt * 9)
        parts.append(fade((voz * metal + rasp) * env, 0.002, 0.03))
    return np.concatenate(parts)


def jetpack_liga():
    # "Fwoosh" de ignição: estalo + chama acendendo e subindo
    sec = 0.8
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    env = np.minimum(1, tt / 0.05) * np.exp(-tt * 3.5)
    fwoosh = lowpass(noise, 400 + 3500 * np.minimum(1, tt / 0.15)) * env
    pop = sweep(220, 70, sec) * np.exp(-tt * 25) * 0.9
    return fade(fwoosh * 1.3 + pop, 0.002, 0.15)


def jetpack():
    # Chiado do motor em loop sem emenda: sopro + ronco grave + leve tremulação
    sec, cross = 2.0, 0.25
    total = t(sec + cross)
    noise = rng.standard_normal(len(total))
    hiss = lowpass(noise, 2600) - lowpass(noise, 500)
    rumble = lowpass(noise, 140) * 2.2
    flutter = 1 + 0.12 * np.sin(2 * np.pi * 7 * total) + 0.06 * np.sin(2 * np.pi * 13 * total)
    x = (hiss * 0.8 + rumble) * flutter
    n, f = int(sec * SR), int(cross * SR)
    out = x[:n].copy()
    ramp = np.linspace(0, 1, f)
    out[:f] = x[:f] * ramp + x[n:n + f] * (1 - ramp)  # fim emenda no começo
    return out


def ronco():
    # Ronco em loop: inspira roncando (grave tremido), solta o ar baixinho, pausa
    sec = 3.4
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    insp = (tt < 1.3) * np.sin(np.pi * np.clip(tt / 1.3, 0, 1)) ** 1.5
    expi = ((tt > 1.5) & (tt < 2.7)) * np.sin(np.pi * np.clip((tt - 1.5) / 1.2, 0, 1)) ** 2
    rattle = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 38 * tt))  # vibração do ronco
    snore = lowpass(noise, 700) * rattle * insp + sweep(70, 95, sec) * 0.6 * insp * rattle
    breath = (lowpass(noise, 1800) - lowpass(noise, 400)) * expi * 0.35
    return snore + breath


def aviso():
    # "Plim-plom" suave de lembrete: dois tons de sino
    parts = []
    for f, sec in ((880, 0.35), (1318.5, 0.6)):
        tt = t(sec)
        bell = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.01 * tt) + 0.15 * np.sin(2 * np.pi * f * 3.02 * tt)
        parts.append(bell * np.exp(-tt * 5) * np.minimum(1, tt / 0.004))
    return fade(np.concatenate(parts), 0.002, 0.08)


def brainblast():
    # Zumbido elétrico subindo + estalos + "ZAP" final
    sec = 2.2
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    rise = np.clip(tt / 1.5, 0, 1)
    buzz = np.sign(np.sin(2 * np.pi * np.cumsum(90 + 260 * rise) / SR)) * 0.25 * rise
    crack = np.zeros(len(tt))
    for _ in range(90):
        i = int(rng.uniform(0.2, 1.6) ** 1.5 / 1.6 ** 0.5 * SR)
        n = int(0.003 * SR)
        if i + n < len(tt): crack[i:i + n] += rng.standard_normal(n) * 0.7
    zap_t = tt - 1.55
    zap = (zap_t > 0) * (lowpass(noise, 6000) * 0.8 + sweep(1800, 200, sec) * 0.6) * np.exp(-np.clip(zap_t, 0, None) * 6)
    return fade(buzz + lowpass(crack, 5000) + zap, 0.01, 0.15)


def fogos():
    # Assobio subindo + estouro + estalinhos
    sec = 2.4
    tt = t(sec)
    noise = rng.standard_normal(len(tt))
    whistle = (tt < 0.7) * sweep(900, 2200, sec, 0.7) * 0.25 * np.minimum(1, tt / 0.1)
    bt = tt - 0.75
    boom = (bt > 0) * (lowpass(noise, 1500) * 1.2 + sweep(90, 40, sec) * 0.9) * np.exp(-np.clip(bt, 0, None) * 5)
    crack = np.zeros(len(tt))
    for _ in range(70):
        i = int(rng.uniform(0.85, 2.1) * SR)
        n = int(0.002 * SR)
        if i + n < len(tt): crack[i:i + n] += rng.standard_normal(n) * 0.5
    return fade(whistle + boom + crack, 0.005, 0.2)


def bolinha():
    # "Boing" curtinho do quique
    sec = 0.18
    tt = t(sec)
    return fade(sweep(420, 260, sec, 0.5) * np.exp(-tt * 22), 0.001, 0.03)


def laser():
    # "Piu" de laser: descida rápida de tom com um pouco de harmônico
    sec = 0.16
    tt = t(sec)
    x = sweep(1800, 400, sec, 0.6) + 0.3 * sweep(3600, 800, sec, 0.6)
    return fade(x * np.exp(-tt * 14), 0.001, 0.03)


def estouro():
    # Meteoro estourando: ruído grave curto com "crack" no começo
    sec = 0.35
    tt = t(sec)
    ruido = lowpass(rng.standard_normal(len(tt)), 900 * np.exp(-tt * 6) + 120)
    crack = rng.standard_normal(len(tt)) * np.exp(-tt * 60)
    return fade((ruido * 1.4 + crack * 0.5) * np.exp(-tt * 9), 0.001, 0.05)


SONS = {"explosao": explosao, "decolagem": decolagem, "paraquedas": paraquedas,
        "pouso": pouso, "goddard": goddard, "latido": latido,
        "jetpack_liga": jetpack_liga, "jetpack": jetpack, "ronco": ronco,
        "aviso": aviso, "brainblast": brainblast, "fogos": fogos, "bolinha": bolinha,
        "laser": laser, "estouro": estouro}

if __name__ == "__main__":
    todos = "--todos" in sys.argv
    for name, fn in SONS.items():
        path = os.path.join(OUT, name + ".wav")
        if os.path.exists(path) and not todos:
            print(f"{name}.wav já existe (mantido)")
            continue
        save(name, fn(), peak={"goddard": 0.5, "latido": 0.5, "jetpack": 0.3, "jetpack_liga": 0.6, "ronco": 0.3, "aviso": 0.5, "brainblast": 0.6, "fogos": 0.6, "bolinha": 0.4, "laser": 0.35, "estouro": 0.6}.get(name, 0.85))
        print(f"{name}.wav criado")
