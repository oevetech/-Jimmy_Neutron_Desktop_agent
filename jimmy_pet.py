import sys
import random
import math
import traceback
import os
import json
import shutil
import time
import re
import datetime
import threading
import urllib.request
import urllib.parse
import urllib.error
import socket
import ctypes
from ctypes import wintypes
import winreg
import subprocess
from PyQt6.QtWidgets import (QApplication, QLabel, QWidget, QPushButton, QSystemTrayIcon, QMenu,
                             QSlider, QSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QComboBox, QGroupBox, QTabWidget, QLineEdit, QListWidget, QTimeEdit,
                             QInputDialog, QMessageBox, QFileDialog, QDateEdit, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, QUrl, pyqtSignal, QObject, QTime, QDate
from PyQt6.QtMultimedia import QSoundEffect, QMediaDevices
from PyQt6.QtNetwork import QUdpSocket, QHostAddress
from PyQt6.QtGui import QPixmap, QTransform, QIcon, QPainter, QColor, QRadialGradient, QPolygon, QPen, QCursor, QDesktopServices

# Imagens e sons: dentro do próprio .exe (PyInstaller extrai em sys._MEIPASS); rodando o .py, de C:\Jimmy
if getattr(sys, "frozen", False):
    RES_DIR = os.path.join(sys._MEIPASS, "recursos")
else:
    _AQUI = os.path.dirname(os.path.abspath(globals().get("__file__", "")))
    if os.path.isdir(os.path.join(_AQUI, "assets", "anim")):
        RES_DIR = os.path.join(_AQUI, "assets")
    else:
        RES_DIR = os.path.join("C:" + os.sep, "Jimmy")
IMG_DIR = os.path.join(RES_DIR, "extracted")
# Configurações e log: pasta do usuário, existe em qualquer PC
DATA_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "JimmyNeutronPet")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "jimmy_error.log")

def log_error(e):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("--- ERRO DETECTADO ---\n")
        traceback.print_exception(type(e), e, e.__traceback__, file=f)
        f.write("\n---------------------\n")

ANIM_DIR = os.path.join(RES_DIR, "anim")
# Configurações salvas pela janela "⚙️ Configurações" do ícone da bandeja
CONFIG_FILE = os.path.join(DATA_DIR, "config_pet.json")
_OLD_CONFIG = os.path.join("C:" + os.sep, "Jimmy", "config_pet.json")
if not os.path.exists(CONFIG_FILE) and os.path.exists(_OLD_CONFIG):
    shutil.copyfile(_OLD_CONFIG, CONFIG_FILE)  # aproveita a configuração antiga deste PC
CONFIG_PADRAO = {"tamanho": 75, "tamanho_goddard": 100, "viagem_min": 1, "viagem_max": 5, "goddard": True, "botao_lancar": True,
                 "sons": True, "volume": 70, "saida_som": "", "esconder_tela_cheia": True,
                 "dormir": True, "vel_foguete": "medio",
                 "som_jimmy": True, "som_goddard": True, "som_foguete": True, "som_ronco": True,
                 "avisos": True, "som_avisos": True, "foguete_x": None, "foguete_aleatorio": True,
                 "ideias": True, "ausente": True, "ausente_min": 10,
                 "datas": True, "aniv_dia": 0, "aniv_mes": 0, "comemorado": "", "amigos": True,
                 "monitor": -1, "frases": True, "bateria": True,
                 "pomodoro_foco": 25, "pomodoro_pausa": 5,
                 "clima": True, "cidade": "", "chuva_tela": True, "clima_dia": "",
                 "stats": {}, "conquistas": [], "meus_lembretes": [], "tom_noite": True,
                 "invencoes": True, "lhamas": True, "dancar": True,
                 "estacoes": True, "easter_egg": False, "rede": False, "curiosidades": True, "idioma": "pt", "passeios": True,
                 "goddard_pet": True, "busca_mouse": True, "consertos": True, "resgate_lhama": True, "game_recorde": 0, "divulgar": True, "divulga_prox": 0, "notas": [], "agua_hoje": {}, "gd_stats": {}, "meteoros": True, "meteoros_recorde": 0, "contagens": [],
                 "repo_github": "oevetech/-Jimmy_Neutron_Desktop_agent", "atualizar": True,
                 "atualizar_sozinho": True, "avisou_versao": "",
                 "apps_reagir": True, "apps": {
                     "spotify.exe": "Solta o som! 🎵", "code.exe": "Hora de programar! 💻",
                     "steam.exe": "Bora jogar! 🎮", "discord.exe": "Manda um oi pros amigos! 👋",
                     "winword.exe": "Escrevendo algo genial? 📝", "excel.exe": "Planilhas... que emoção! 📊",
                     "obs64.exe": "Gravando vídeo pro canal? 🎬", "blender.exe": "Modelando em 3D? 🧊",
                     "photoshop.exe": "Hora da arte! 🎨"},
                 "aviso_agua": True, "aviso_agua_min": 60,
                 "aviso_pausa": True, "aviso_pausa_min": 50,
                 "aviso_comer": True, "aviso_comer_min": 240,
                 "aviso_exercicio": True, "aviso_exercicio_min": 90,
                 "aviso_dormir": True}

# Velocidade da subida do foguete (Rápido = como era antes)
VEL_FOGUETE = [("bem_lento", "Bem lento", 0.35), ("medio", "Médio", 0.55),
               ("normal", "Normal", 0.75), ("rapido", "Rápido", 1.0)]

def vel_foguete():
    return {k: f for k, _, f in VEL_FOGUETE}.get(CFG["vel_foguete"], 1.0)

# De vez em quando (12 a 36 h) o Jimmy lembra do canal de quem criou o pet
CANAL_URL = "https://www.youtube.com/@oevetech"
FRASES_CANAL = [
    "Psiu! Já conhece o canal @oevetech no YouTube? ▶️ Clica em mim!",
    "Quem me trouxe pro seu PC foi o @oevetech! Dá uma passada lá ▶️",
    "Ideia genial: se inscrever no @oevetech! 💡▶️",
    "O Goddard aprovou o canal @oevetech! 🐕 Clica em mim pra ver ▶️",
    "Tem vídeo novo de tecnologia no @oevetech? Vamos ver! ▶️",
]

# Frases do Jimmy quando a ideia chega (Brain Blast)
IDEIAS = ["Tive uma ideia! 💡", "Eureka! 💡", "Já sei! 🤓", "Gotta blast! 🚀", "Isso vai funcionar! 🔬"]

# Visitas dos amigos: cada conversa é uma lista de (quem fala, texto)
CONVERSAS = {
    "carl": [
        [("amigo", "Oi, Jimmy! 👋"), ("jimmy", "E aí, Carl!"), ("amigo", "Você viu minhas lhamas? 🦙"),
         ("jimmy", "De novo, Carl?"), ("amigo", "Elas fugiram outra vez! Tchau!")],
        [("amigo", "Jimmy! Trouxe biscoitos! 🍪"), ("jimmy", "Valeu, Carl!"),
         ("amigo", "Ops... comi todos no caminho. 😅"), ("jimmy", "Típico..."), ("amigo", "Tchau, Jimmy!")],
        [("amigo", "Oi, Goddard! Oi, Jimmy!"), ("jimmy", "Oi, Carl! Tudo bem?"),
         ("amigo", "Minha alergia atacou de novo... 🤧"), ("jimmy", "Saúde!"), ("amigo", "Valeu! Até mais!")],
    ],
    "sheen": [
        [("amigo", "JIMMY! 🤖"), ("jimmy", "Oi, Sheen!"), ("amigo", "Ultra Lord vai salvar o mundo hoje!"),
         ("jimmy", "Claro que vai, Sheen..."), ("amigo", "ULTRA LORD! Tchau!")],
        [("amigo", "E aí, Jimmy! Bora brincar?"), ("jimmy", "Agora não, tô inventando!"),
         ("amigo", "Inventa um robô do Ultra Lord! 🤩"), ("jimmy", "Vou pensar..."), ("amigo", "Você é o melhor! Fui!")],
        [("amigo", "Jimmy! Vi um disco voador! 🛸"), ("jimmy", "Sério?!"),
         ("amigo", "Não... era um prato. 😅"), ("jimmy", "Hahaha!"), ("amigo", "Até mais, gênio!")],
    ],
    "cindy": [
        [("amigo", "NEUTRON!"), ("jimmy", "Ah, oi Cindy... 😒"), ("amigo", "Meu projeto de ciências é MUITO melhor que o seu!"),
         ("jimmy", "Duvido! Meu foguete voa! 🚀"), ("amigo", "E explode também... 🙄 Hmpf!")],
        [("amigo", "Neutron! Você explodiu meu jardim de novo!"), ("jimmy", "Foi um acidente científico!"),
         ("amigo", "Você é um perigo ambulante!"), ("jimmy", "Pelo menos não sou chata! 😜"), ("amigo", "Argh! Hmpf! 😤")],
        [("amigo", "Olha só, o gênio do bairro..."), ("jimmy", "Olha só, a sabe-tudo..."),
         ("amigo", "Eu tirei 10 na prova! 📝"), ("jimmy", "Eu tirei 10,5! 😎"), ("amigo", "Isso nem existe, Neutron! Hmpf!")],
    ],
    "libby": [
        [("amigo", "Oi, Jimmy! 🎵"), ("jimmy", "Oi, Libby!"), ("amigo", "Bora ouvir uma música nova?"),
         ("jimmy", "Depois! Tô num experimento."), ("amigo", "Tá bom, gênio. Tchau! 😉")],
        [("amigo", "Jimmy, a Cindy tá te procurando!"), ("jimmy", "Ih... de novo?"),
         ("amigo", "Disse que você estragou o projeto dela."), ("jimmy", "Foi um acidente científico!"),
         ("amigo", "Hahaha! Boa sorte! 👋")],
        [("amigo", "Que invenção é essa, Jimmy?"), ("jimmy", "Um foguete turbo! 🚀"),
         ("amigo", "Só não explode de novo, tá?"), ("jimmy", "...sem promessas."), ("amigo", "Hahaha! Tchau!")],
    ],
}

# Datas comemorativas: (mês, dia) -> (mensagem, efeito)
DATAS = {(12, 24): ("Feliz véspera de Natal! 🎄", "natal"), (12, 25): ("Feliz Natal! 🎄", "natal"),
         (12, 31): ("Feliz Ano Novo! 🎆", "fogos"), (1, 1): ("Feliz Ano Novo! 🎆", "fogos"),
         (10, 31): ("Feliz Halloween! 🎃", "halloween"), (10, 12): ("Feliz Dia das Crianças! 🎈", "confete")}

def data_especial(tm):
    if CFG["aniv_dia"] and CFG["aniv_mes"] and (tm.tm_mon, tm.tm_mday) == (CFG["aniv_mes"], CFG["aniv_dia"]):
        return ("Feliz aniversário! 🎂🎉", "confete")
    return DATAS.get((tm.tm_mon, tm.tm_mday))

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

def idle_seconds():
    """Há quantos segundos o mouse e o teclado estão parados."""
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)): return 0.0
    return ((ctypes.windll.kernel32.GetTickCount() - lii.dwTime) & 0xFFFFFFFF) / 1000.0

# Lembretes: animação, texto do balão e chave de configuração
AVISOS = {
    "agua":      "Hora de beber água! 💧",
    "pausa":     "Faça uma pausa e descanse os olhos 😌",
    "comer":     "Não esqueça de comer! 🍎",
    "exercicio": "Hora de se mexer um pouco! 💪",
    "dormir":    "Hora de dormir! Boa noite 💤",
}

def load_cfg():
    cfg = dict(CONFIG_PADRAO)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg

def save_cfg(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError as e:
        log_error(e)

CFG = load_cfg()
CFG["stats"] = dict(CFG.get("stats") or {})
CFG["conquistas"] = list(CFG.get("conquistas") or [])
CFG["meus_lembretes"] = [dict(l) for l in (CFG.get("meus_lembretes") or [])]
CFG["apps"] = dict(CFG.get("apps") or {})
CFG["contagens"] = [dict(c) for c in (CFG.get("contagens") or [])]
CFG["notas"] = [dict(n) for n in (CFG.get("notas") or [])]
CFG["gd_stats"] = dict(CFG.get("gd_stats") or {})

# ---------- Goddard bichinho virtual: óleo (fome), diversão e limpeza, de 0 a 100 ----------
GD_ITENS = (("oleo", "🛢️"), ("diversao", "🎾"), ("limpeza", "🛁"))
GD_QUEDA = {"oleo": 0.35, "diversao": 0.5, "limpeza": 0.25}   # pontos por minuto

def gd_iniciar():
    st = CFG["gd_stats"]
    for k, _ in GD_ITENS: st.setdefault(k, 80.0)
    # Com o pet fechado o tempo passa também (pela metade, no máximo 2 dias)
    if st.get("ts"):
        mins = min(2880, max(0, (time.time() - st["ts"]) / 60))
        for k, q in GD_QUEDA.items(): st[k] = max(0.0, st[k] - q * mins * 0.5)
    st["ts"] = time.time()

def gd_get(k):
    return CFG["gd_stats"].get(k, 80.0)

def gd_add(k, n):
    CFG["gd_stats"][k] = max(0.0, min(100.0, gd_get(k) + n))

APP_VERSAO = "1.1"   # suba este número a cada versão publicada no GitHub

def versao_tupla(v):
    try: return tuple(int(x) for x in str(v).lstrip("vV").split("."))
    except ValueError: return (0,)

# ---------- Estações (hemisfério sul) ----------
def estacao_atual(tm=None):
    tm = tm or time.localtime()
    md = (tm.tm_mon, tm.tm_mday)
    if tm.tm_mon == 12: return "neve"
    if (3, 20) <= md < (6, 21): return "outono"
    if (9, 23) <= md <= (11, 30): return "primavera"
    return None

# ---------- Programa em foco (para o Jimmy comentar) ----------
def exe_em_foco():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd: return ""
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
        if not h: return ""
        try:
            buf = ctypes.create_unicode_buffer(520)
            n = wintypes.DWORD(520)
            if not ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)): return ""
            return os.path.basename(buf.value).lower()
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
    except OSError:
        return ""

# ---------- Lembretes personalizados ----------
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
REPETICOES = [("uma", "Uma vez"), ("diario", "Todo dia"), ("uteis", "Dias úteis (seg–sex)")] + \
             [(f"sem{i}", ("Todo " if i >= 5 else "Toda ") + d) for i, d in enumerate(DIAS)]

def lembrete_hoje(l, tm):
    rep = l.get("rep", "diario")
    if rep == "uma": return l.get("data") == time.strftime("%Y-%m-%d", tm)
    if rep == "diario": return True
    if rep == "uteis": return tm.tm_wday < 5
    return rep == f"sem{tm.tm_wday}"

def novo_lembrete(texto, hora, rep):
    l = {"texto": texto, "hora": hora, "rep": rep, "ultimo": ""}
    if rep == "uma":
        # Hoje, se ainda não passou do horário; senão amanhã
        hoje = time.strftime("%Y-%m-%d")
        amanha = time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400))
        l["data"] = hoje if hora > time.strftime("%H:%M") else amanha
    CFG["meus_lembretes"].append(l)
    save_cfg(CFG)
    return l

def lembrete_texto(l):
    nome = dict(REPETICOES).get(l.get("rep"), "")
    if l.get("rep") == "uma" and l.get("data"):
        a, mth, d = l["data"].split("-")
        nome += f" ({d}/{mth})"
    return f"⏰ {l['hora']} · {nome} — {l['texto']}"

# ---------- Tom de noite ----------
def noite_tint():
    """0 de dia, 1 à noite; transição das 17h às 19h e das 5h às 6h. Em degraus de 25%."""
    if not CFG.get("tom_noite", True): return 0.0
    tm = time.localtime()
    h = tm.tm_hour + tm.tm_min / 60
    if 6 <= h < 17: x = 0.0
    elif 17 <= h < 19: x = (h - 17) / 2
    elif 5 <= h < 6: x = 6 - h
    else: x = 1.0
    return round(x * 4) / 4

# ---------- Monitor escolhido (os pets trabalham em coordenadas do monitor; OX/OY desloca) ----------
OX = OY = 0

TELAS = []   # [(x0, x1, chão)] em coordenadas do pet; com "todos", um por monitor

def tela_geo():
    telas = QApplication.screens()
    i = CFG.get("monitor", -1)
    if i == -2 and len(telas) > 1:
        # Todos os monitores: área que junta todos (o pet anda de um para o outro)
        geo = telas[0].geometry()
        for t in telas[1:]:
            geo = geo.united(t.geometry())
        return geo
    if isinstance(i, int) and 0 <= i < len(telas):
        return telas[i].geometry()
    return QApplication.primaryScreen().geometry()

def atualizar_telas():
    """Monta a lista de monitores (faixa horizontal e chão de cada um) relativa à área do pet."""
    global TELAS
    geo = tela_geo()
    if CFG.get("monitor", -1) == -2 and len(QApplication.screens()) > 1:
        TELAS = sorted((t.geometry().x() - geo.x(), t.geometry().x() - geo.x() + t.geometry().width(),
                        t.geometry().y() - geo.y() + t.geometry().height()) for t in QApplication.screens())
    else:
        TELAS = [(0, geo.width(), geo.height())]

def chao_em(x):
    """Linha do chão (borda de baixo) do monitor que está embaixo do ponto x."""
    if not TELAS: return None
    for x0, x1, chao in TELAS:
        if x0 <= x < x1:
            return chao
    return min(TELAS, key=lambda t: min(abs(x - t[0]), abs(x - t[1])))[2]

# ---------- Não perturbe / Pomodoro ----------
QUIET_UNTIL = 0.0
MANAGER = None

def nao_perturbe():
    return time.time() < QUIET_UNTIL

def quieto():
    """Sem distrações: não perturbe ligado ou Pomodoro em foco."""
    pomo = getattr(MANAGER, "pomo", None)
    return nao_perturbe() or (pomo is not None and pomo["estado"] == "foco")

# ---------- Conquistas ----------
CONQUISTAS = [
    ("voo1", "lancamentos", 1, "🚀 Primeiro voo"), ("voo10", "lancamentos", 10, "🧑‍🚀 Piloto de testes"),
    ("voo50", "lancamentos", 50, "🌌 Astronauta"), ("bola1", "bolinhas", 1, "🎾 Pega, Goddard!"),
    ("bola20", "bolinhas", 20, "🐕 Melhor amigo do cão"), ("vento1", "rajadas", 1, "🌪️ Levado pelo vento"),
    ("vento5", "rajadas", 5, "🌬️ Rei do vento"), ("amigo1", "amigos", 1, "👋 Visita surpresa"),
    ("amigo10", "amigos", 10, "👫 Popular"), ("blast5", "blasts", 5, "⚡ Mente brilhante"),
    ("arrasto10", "arrastos", 10, "🖐️ Mão boba"), ("foco1", "focos", 1, "🍅 Primeiro foco"),
    ("foco10", "focos", 10, "🧘 Mestre do foco"), ("festa1", "festas", 1, "🎉 Hora da festa"),
    ("aviso10", "avisos", 10, "💧 Saúde em dia"),
    ("inv5", "invencoes", 5, "🧪 Cientista maluco"), ("lhama3", "lhamas", 3, "🦙 Caçador de lhamas"),
    ("danca5", "dancas", 5, "💃 Pé de valsa"), ("passeio5", "passeios", 5, "🛸 Piloto de passeio"),
    ("cuidado20", "cuidados", 20, "🐶 Dono responsável"), ("resgate1", "resgates", 1, "🪐 Resgate espacial"), ("game1", "game_partidas", 1, "🕹️ Piloto de combate"),
    ("ondas10", "game_ondas", 10, "🛡️ Defensor de Retroville"), ("conserto5", "consertos", 5, "🔧 Mecânico genial"), ("agua50", "copos", 50, "💧 Hidratado de verdade"), ("ponteiro1", "ponteiros", 1, "🖱️ Cadê meu mouse?"), ("meteoro50", "meteoros", 50, "☄️ Caçador de meteoros"),
]

def stat(nome, n=1):
    """Conta uma ação e libera conquistas (o Jimmy comemora quando puder)."""
    CFG["stats"][nome] = CFG["stats"].get(nome, 0) + n
    for cid, st, alvo, titulo in CONQUISTAS:
        if st == nome and cid not in CFG["conquistas"] and CFG["stats"][nome] >= alvo:
            CFG["conquistas"].append(cid)
            if MANAGER:
                MANAGER.queue.append(("party", f"🏆 Conquista: {titulo}!", "confete", False))
                if MANAGER.config_window and MANAGER.config_window.isVisible():
                    MANAGER.config_window.carregar_conquistas()
    save_cfg(CFG)

# ---------- Curiosidades científicas ----------
CURIOSIDADES = [
    "Um raio é cerca de 5 vezes mais quente que a superfície do Sol! ⚡",
    "A luz do Sol leva uns 8 minutos para chegar à Terra! ☀️",
    "Os polvos têm três corações! 🐙",
    "Um dia em Vênus dura mais que um ano em Vênus! 🪐",
    "O cérebro humano tem cerca de 86 bilhões de neurônios! 🧠",
    "No ponto triplo, a água ferve e congela ao mesmo tempo! 💧",
    "Os tubarões existem há mais tempo que as árvores! 🦈",
    "Bananas são levemente radioativas, por causa do potássio! 🍌",
    "O som não se propaga no vácuo do espaço! 🔇",
    "Há mais estrelas no universo do que grãos de areia nas praias da Terra! ✨",
    "Um ano-luz tem cerca de 9,46 trilhões de quilômetros! 🔭",
    "O coração de uma baleia-azul pode pesar mais de 150 kg! 🐋",
    "A Torre Eiffel fica até 15 cm mais alta no verão: o metal dilata! 🗼",
    "Os flamingos são cor-de-rosa por causa do que comem! 🦩",
    "O mel quase não estraga: acharam mel comestível em tumbas egípcias! 🍯",
    "A Lua se afasta da Terra cerca de 3,8 cm por ano! 🌙",
    "O DNA de uma única célula, esticado, teria uns 2 metros! 🧬",
    "Diamante e o grafite do lápis são feitos do mesmo elemento: carbono! 💎",
    "Marte tem o maior vulcão do Sistema Solar: o Monte Olimpo! 🌋",
    "Os golfinhos dormem com metade do cérebro de cada vez! 🐬",
    "A luz viaja a quase 300 mil km por segundo! 💡",
    "Júpiter tem mais de 90 luas conhecidas! 🪐",
    "Um átomo é quase todo espaço vazio! ⚛️",
    "A Grande Muralha da China NÃO dá para ver a olho nu do espaço! 🚀",
    "A cauda de um cometa sempre aponta para longe do Sol! ☄️",
    "As formigas não têm pulmões: respiram por furinhos no corpo! 🐜",
    "O vidro é feito principalmente de areia! 🏖️",
    "A gente pisca umas 15 a 20 vezes por minuto! 👁️",
    "Saturno é tão pouco denso que boiaria numa banheira gigante! 🛁",
    "A Estação Espacial dá uma volta na Terra a cada ~90 minutos! 🛰️",
]


# ======================= Idioma: inglês =======================
# Textos em português -> inglês. O que não estiver aqui continua em português.
EN = {
    # --- falas do Jimmy ---
    "Pensa, pensa, pensa! 🤔": "Think, think, think! 🤔", "Pensa, pensa, pensa... 🤔": "Think, think, think... 🤔",
    "Goddard, analise! 🐕": "Goddard, analyze! 🐕", "Bateria de cérebro carregada! 🔋": "Brain battery charged! 🔋",
    "A ciência resolve tudo! 🔬": "Science solves everything! 🔬", "Gotta blast! 🚀": "Gotta blast! 🚀",
    "Mais uma invenção vindo aí... 💡": "Another invention coming up... 💡", "Não toque no foguete! 😅": "Don't touch the rocket! 😅",
    "Precisa de ajuda? 🤓": "Need some help? 🤓", "Meu QI é de 210! 🧠": "My IQ is 210! 🧠",
    "Cuidado: alto risco de explosão! 💥": "Careful: high risk of explosion! 💥",
    "Tive uma ideia! 💡": "I've got an idea! 💡", "Eureka! 💡": "Eureka! 💡", "Já sei! 🤓": "I know! 🤓",
    "Isso vai funcionar! 🔬": "This is going to work! 🔬", "BRAIN BLAST! ⚡": "BRAIN BLAST! ⚡",
    "Uaaaau! 🌪️": "Whoooa! 🌪️", "Voltou! 👋": "You're back! 👋", "🎵 Essa música é boa!": "🎵 This song is great!",
    "Hora de inventar! 🔧": "Time to invent! 🔧", "Ops... 😅 De volta à prancheta!": "Oops... 😅 Back to the drawing board!",
    "Testando o raio encolhedor! 🔫": "Testing the shrink ray! 🔫", "Hahaha! Olha o tamanho dele! 😆": "Hahaha! Look how tiny he is! 😆",
    "Pronto, voltou ao normal! 😅": "There, back to normal! 😅", "Modo cientista! 🥽": "Scientist mode! 🥽",
    "Goddard, pula! 🎮": "Goddard, jump! 🎮", "De novo, Carl? 🙄": "Again, Carl? 🙄",
    "As lhamas fugiram outra vez! 🦙": "The llamas ran away again! 🦙", "Corre, Carl! 😂": "Run, Carl! 😂",
    "Pomodoro parado. 🍅": "Pomodoro stopped. 🍅", "Timers cancelados. ⏱️": "Timers canceled. ⏱️",
    "Ninguém em casa... 🤷": "Nobody home... 🤷", "O Jimmy de lá tá ocupado! 😅": "The other Jimmy is busy! 😅",
    "Não achei nenhum PC com o pet na rede. 📡": "I didn't find any PC with the pet on the network. 📡",
    "Baixando a versão nova... ⏬": "Downloading the new version... ⏬", "Deu o tempo!": "Time's up!",
    "Uau! Boa viagem! 🚀": "Wow! Have a nice trip! 🚀",
    "Minhas lhamas! 🦙": "My llamas! 🦙", "Volta aqui, lhaminha! 😱": "Come back, little llama! 😱",
    "Alguém segura essa lhama! 🦙": "Somebody stop that llama! 🦙",
    # --- avisos, datas, pomodoro ---
    "Hora de beber água! 💧": "Time to drink some water! 💧", "Faça uma pausa e descanse os olhos 😌": "Take a break and rest your eyes 😌",
    "Não esqueça de comer! 🍎": "Don't forget to eat! 🍎", "Hora de se mexer um pouco! 💪": "Time to move around a bit! 💪",
    "Hora de dormir! Boa noite 💤": "Time for bed! Good night 💤",
    "Feliz véspera de Natal! 🎄": "Merry Christmas Eve! 🎄", "Feliz Natal! 🎄": "Merry Christmas! 🎄",
    "Feliz Ano Novo! 🎆": "Happy New Year! 🎆", "Feliz Halloween! 🎃": "Happy Halloween! 🎃",
    "Feliz Dia das Crianças! 🎈": "Happy Children's Day! 🎈", "Feliz aniversário! 🎂🎉": "Happy birthday! 🎂🎉",
    "Fim da pausa! Bora focar? 🍅": "Break's over! Ready to focus? 🍅",
    # --- conversas: Carl ---
    "Oi, Jimmy! 👋": "Hi, Jimmy! 👋", "E aí, Carl!": "Hey, Carl!", "Você viu minhas lhamas? 🦙": "Have you seen my llamas? 🦙",
    "De novo, Carl?": "Again, Carl?", "Elas fugiram outra vez! Tchau!": "They ran away again! Bye!",
    "Jimmy! Trouxe biscoitos! 🍪": "Jimmy! I brought cookies! 🍪", "Valeu, Carl!": "Thanks, Carl!",
    "Ops... comi todos no caminho. 😅": "Oops... I ate them all on the way. 😅", "Típico...": "Typical...",
    "Tchau, Jimmy!": "Bye, Jimmy!", "Oi, Goddard! Oi, Jimmy!": "Hi, Goddard! Hi, Jimmy!",
    "Oi, Carl! Tudo bem?": "Hi, Carl! How are you?", "Minha alergia atacou de novo... 🤧": "My allergies are acting up again... 🤧",
    "Saúde!": "Bless you!", "Valeu! Até mais!": "Thanks! See you!",
    # --- conversas: Sheen ---
    "JIMMY! 🤖": "JIMMY! 🤖", "Oi, Sheen!": "Hi, Sheen!", "Ultra Lord vai salvar o mundo hoje!": "Ultra Lord is going to save the world today!",
    "Claro que vai, Sheen...": "Sure he is, Sheen...", "ULTRA LORD! Tchau!": "ULTRA LORD! Bye!",
    "E aí, Jimmy! Bora brincar?": "Hey, Jimmy! Wanna play?", "Agora não, tô inventando!": "Not now, I'm inventing!",
    "Inventa um robô do Ultra Lord! 🤩": "Invent an Ultra Lord robot! 🤩", "Vou pensar...": "I'll think about it...",
    "Você é o melhor! Fui!": "You're the best! Gotta go!", "Jimmy! Vi um disco voador! 🛸": "Jimmy! I saw a flying saucer! 🛸",
    "Sério?!": "Really?!", "Não... era um prato. 😅": "Nope... it was a plate. 😅", "Hahaha!": "Hahaha!",
    "Até mais, gênio!": "See you, genius!",
    # --- conversas: Cindy ---
    "NEUTRON!": "NEUTRON!", "Ah, oi Cindy... 😒": "Oh, hi Cindy... 😒",
    "Meu projeto de ciências é MUITO melhor que o seu!": "My science project is WAY better than yours!",
    "Duvido! Meu foguete voa! 🚀": "I doubt it! My rocket flies! 🚀", "E explode também... 🙄 Hmpf!": "And explodes too... 🙄 Hmph!",
    "Neutron! Você explodiu meu jardim de novo!": "Neutron! You blew up my garden again!",
    "Foi um acidente científico!": "It was a scientific accident!", "Você é um perigo ambulante!": "You're a walking disaster!",
    "Pelo menos não sou chata! 😜": "At least I'm not annoying! 😜", "Argh! Hmpf! 😤": "Argh! Hmph! 😤",
    "Olha só, o gênio do bairro...": "Well, look, the neighborhood genius...", "Olha só, a sabe-tudo...": "Well, look, Miss Know-It-All...",
    "Eu tirei 10 na prova! 📝": "I got an A on the test! 📝", "Eu tirei 10,5! 😎": "I got an A+! 😎",
    "Isso nem existe, Neutron! Hmpf!": "Whatever, Neutron! Hmph!",
    # --- conversas: Libby ---
    "Oi, Jimmy! 🎵": "Hi, Jimmy! 🎵", "Oi, Libby!": "Hi, Libby!", "Bora ouvir uma música nova?": "Wanna listen to a new song?",
    "Depois! Tô num experimento.": "Later! I'm in the middle of an experiment.", "Tá bom, gênio. Tchau! 😉": "Okay, genius. Bye! 😉",
    "Jimmy, a Cindy tá te procurando!": "Jimmy, Cindy is looking for you!", "Ih... de novo?": "Uh-oh... again?",
    "Disse que você estragou o projeto dela.": "She says you ruined her project.", "Hahaha! Boa sorte! 👋": "Hahaha! Good luck! 👋",
    "Que invenção é essa, Jimmy?": "What invention is that, Jimmy?", "Um foguete turbo! 🚀": "A turbo rocket! 🚀",
    "Só não explode de novo, tá?": "Just don't blow it up again, okay?", "...sem promessas.": "...no promises.",
    "Hahaha! Tchau!": "Hahaha! Bye!",
    # --- visitante da rede ---
    "Um Jimmy de outro PC?! 😮": "A Jimmy from another PC?! 😮", "Lá também tem foguete! 🚀": "There's a rocket there too! 🚀",
    "Ciência de rede! 📡": "Network science! 📡", "Tenho que voltar. Tchau!": "I have to go back. Bye!",
    "Uau, viajou pelo cabo de rede?": "Wow, did you travel through the network cable?",
    "Pelo Wi-Fi, é mais rápido! 😎": "By Wi-Fi, it's faster! 😎", "Até a próxima visita! 👋": "See you next visit! 👋",
    # --- apps ---
    "Solta o som! 🎵": "Turn up the music! 🎵", "Hora de programar! 💻": "Time to code! 💻", "Bora jogar! 🎮": "Let's play! 🎮",
    "Manda um oi pros amigos! 👋": "Say hi to your friends! 👋", "Escrevendo algo genial? 📝": "Writing something brilliant? 📝",
    "Planilhas... que emoção! 📊": "Spreadsheets... how exciting! 📊", "Gravando vídeo pro canal? 🎬": "Recording a video for the channel? 🎬",
    "Modelando em 3D? 🧊": "Modeling in 3D? 🧊", "Hora da arte! 🎨": "Art time! 🎨",
    # --- curiosidades ---
    "Um raio é cerca de 5 vezes mais quente que a superfície do Sol! ⚡": "A lightning bolt is about 5 times hotter than the surface of the Sun! ⚡",
    "A luz do Sol leva uns 8 minutos para chegar à Terra! ☀️": "Sunlight takes about 8 minutes to reach Earth! ☀️",
    "Os polvos têm três corações! 🐙": "Octopuses have three hearts! 🐙",
    "Um dia em Vênus dura mais que um ano em Vênus! 🪐": "A day on Venus lasts longer than a year on Venus! 🪐",
    "O cérebro humano tem cerca de 86 bilhões de neurônios! 🧠": "The human brain has about 86 billion neurons! 🧠",
    "No ponto triplo, a água ferve e congela ao mesmo tempo! 💧": "At the triple point, water boils and freezes at the same time! 💧",
    "Os tubarões existem há mais tempo que as árvores! 🦈": "Sharks have existed for longer than trees! 🦈",
    "Bananas são levemente radioativas, por causa do potássio! 🍌": "Bananas are slightly radioactive because of potassium! 🍌",
    "O som não se propaga no vácuo do espaço! 🔇": "Sound can't travel through the vacuum of space! 🔇",
    "Há mais estrelas no universo do que grãos de areia nas praias da Terra! ✨": "There are more stars in the universe than grains of sand on Earth's beaches! ✨",
    "Um ano-luz tem cerca de 9,46 trilhões de quilômetros! 🔭": "A light-year is about 9.46 trillion kilometers! 🔭",
    "O coração de uma baleia-azul pode pesar mais de 150 kg! 🐋": "A blue whale's heart can weigh more than 150 kg! 🐋",
    "A Torre Eiffel fica até 15 cm mais alta no verão: o metal dilata! 🗼": "The Eiffel Tower grows up to 15 cm taller in summer: the metal expands! 🗼",
    "Os flamingos são cor-de-rosa por causa do que comem! 🦩": "Flamingos are pink because of what they eat! 🦩",
    "O mel quase não estraga: acharam mel comestível em tumbas egípcias! 🍯": "Honey almost never spoils: edible honey was found in Egyptian tombs! 🍯",
    "A Lua se afasta da Terra cerca de 3,8 cm por ano! 🌙": "The Moon drifts about 3.8 cm away from Earth every year! 🌙",
    "O DNA de uma única célula, esticado, teria uns 2 metros! 🧬": "The DNA in a single cell, stretched out, would be about 2 meters long! 🧬",
    "Diamante e o grafite do lápis são feitos do mesmo elemento: carbono! 💎": "Diamond and pencil graphite are made of the same element: carbon! 💎",
    "Marte tem o maior vulcão do Sistema Solar: o Monte Olimpo! 🌋": "Mars has the largest volcano in the Solar System: Olympus Mons! 🌋",
    "Os golfinhos dormem com metade do cérebro de cada vez! 🐬": "Dolphins sleep with half of their brain at a time! 🐬",
    "A luz viaja a quase 300 mil km por segundo! 💡": "Light travels at almost 300,000 km per second! 💡",
    "Júpiter tem mais de 90 luas conhecidas! 🪐": "Jupiter has more than 90 known moons! 🪐",
    "Um átomo é quase todo espaço vazio! ⚛️": "An atom is almost entirely empty space! ⚛️",
    "A Grande Muralha da China NÃO dá para ver a olho nu do espaço! 🚀": "The Great Wall of China is NOT visible to the naked eye from space! 🚀",
    "A cauda de um cometa sempre aponta para longe do Sol! ☄️": "A comet's tail always points away from the Sun! ☄️",
    "As formigas não têm pulmões: respiram por furinhos no corpo! 🐜": "Ants have no lungs: they breathe through tiny holes in their bodies! 🐜",
    "O vidro é feito principalmente de areia! 🏖️": "Glass is made mostly of sand! 🏖️",
    "A gente pisca umas 15 a 20 vezes por minuto! 👁️": "We blink about 15 to 20 times a minute! 👁️",
    "Saturno é tão pouco denso que boiaria numa banheira gigante! 🛁": "Saturn is so light it would float in a giant bathtub! 🛁",
    "A Estação Espacial dá uma volta na Terra a cada ~90 minutos! 🛰️": "The Space Station circles Earth every ~90 minutes! 🛰️",
    # --- clima ---
    "céu limpo": "clear sky", "poucas nuvens": "a few clouds", "nublado": "cloudy", "neblina": "fog", "garoa": "drizzle",
    "chuva": "rain", "neve": "snow", "pancadas de chuva": "rain showers", "tempestade": "thunderstorm",
    "tempo instável": "unsettled weather",
    # --- conquistas ---
    "🚀 Primeiro voo": "🚀 First flight", "🧑‍🚀 Piloto de testes": "🧑‍🚀 Test pilot", "🌌 Astronauta": "🌌 Astronaut",
    "🎾 Pega, Goddard!": "🎾 Fetch, Goddard!", "🐕 Melhor amigo do cão": "🐕 Dog's best friend",
    "🌪️ Levado pelo vento": "🌪️ Gone with the wind", "🌬️ Rei do vento": "🌬️ Wind king", "👋 Visita surpresa": "👋 Surprise visit",
    "👫 Popular": "👫 Popular", "⚡ Mente brilhante": "⚡ Brilliant mind", "🖐️ Mão boba": "🖐️ Grabby hands",
    "🍅 Primeiro foco": "🍅 First focus", "🧘 Mestre do foco": "🧘 Focus master", "🎉 Hora da festa": "🎉 Party time",
    "💧 Saúde em dia": "💧 Healthy habits", "🧪 Cientista maluco": "🧪 Mad scientist", "🦙 Caçador de lhamas": "🦙 Llama hunter",
    "💃 Pé de valsa": "💃 Dancing queen", "🛸 Piloto de passeio": "🛸 Joyride pilot",
    "🛸 Passeio de foguete": "🛸 Rocket joyride",
    "🐶 Dono responsável": "🐶 Responsible owner", "☄️ Caçador de meteoros": "☄️ Meteor hunter",
    "🛢️ Dar óleo": "🛢️ Give oil", "🎾 Brincar": "🎾 Play", "🛁 Dar banho": "🛁 Give a bath",
    "Óleo! 😋": "Oil! 😋", "Que limpinho! ✨": "So clean! ✨", "Au au! 🎾": "Woof woof! 🎾",
    "☄️ Chuva de meteoros": "☄️ Meteor shower", "Chuva de meteoros! Clica neles! ☄️": "Meteor shower! Click them! ☄️",
    "🐶 Cuidar do Goddard": "🐶 Take care of Goddard", "☄️ Meteoros": "☄️ Meteors", "☄️ Testar": "☄️ Test",
    "⏳ Datas": "⏳ Dates", "Evento:": "Event:", "Data:": "Date:", "ex.: Viagem de férias": "e.g.: Vacation trip",
    "(nenhuma data ainda)": "(no dates yet)", "⏳ O Jimmy avisa quantos dias faltam e comemora no dia.": "⏳ Jimmy tells you how many days are left and celebrates on the day.",
    "é hoje! 🎉": "it's today! 🎉", "amanhã": "tomorrow",
    "Ei! Para com isso! 😆": "Hey! Stop that! 😆",
    "Tive uma ideia de invenção! 💡 Mas preciso daquele ponteiro...": "I've got an invention idea! 💡 But I need that pointer...",
    "Goddard, pega o ponteiro! 🐕": "Goddard, fetch the pointer! 🐕", "🖱️ Goddard, pega o ponteiro!": "🖱️ Goddard, fetch the pointer!",
    "Valeu, Goddard! Agora sim, vou inventar! 🛠️": "Thanks, Goddard! Now I can invent! 🛠️",
    "Opa, você voltou! Pode ficar com o mouse 😅": "Oops, you're back! You can keep the mouse 😅",
    "🖱️ Buscar o ponteiro": "🖱️ Fetch the pointer",
    "🔧 Consertar o foguete": "🔧 Fix the rocket", "🪐 Resgatar a lhama do planeta": "🪐 Rescue the llama from the planet",
    "🪐 Resgate da lhama": "🪐 Llama rescue", "🪐 Resgate espacial": "🪐 Space rescue",
    "Olha lá em cima! Uma lhama perdida no espaço! 🦙🪐": "Look up there! A llama lost in space! 🦙🪐",
    "Aquilo é... uma lhama num planeta?! 🦙🪐": "Is that... a llama on a planet?! 🦙🪐",
    "Segura aí, Carl! Eu busco! 🚀": "Hang on, Carl! I'll get it! 🚀", "Peguei! Segura firme, lhaminha! 🦙": "Got it! Hold on tight, little llama! 🦙",
    "Jimmy! Minha lhama foi parar naquele planeta! 😱🦙": "Jimmy! My llama ended up on that planet! 😱🦙",
    "Socorro! A lhama tá no espaço! 🦙🪐": "Help! The llama is in space! 🦙🪐", "Vai, Jimmy! 🙏": "Go, Jimmy! 🙏",
    "Cuidado com a lhama! 🦙": "Careful with the llama! 🦙", "Lhaminha!! Valeu, Jimmy! 🦙💕": "My llama!! Thanks, Jimmy! 🦙💕",
    "Você é o melhor, Jimmy! 🦙✨": "You're the best, Jimmy! 🦙✨", "Nunca mais foge, tá? 🦙😭": "Never run away again, okay? 🦙😭", "🕹️ Modo Game": "🕹️ Game mode",
    "🕹️ Piloto de combate": "🕹️ Combat pilot", "🛡️ Defensor de Retroville": "🛡️ Defender of Retroville",
    "Escudo! 🛡️": "Shield! 🛡️", "Rei Goobot derrotado! +1500 👑": "King Goobot defeated! +1500 👑", "⚡ BRAIN BLAST! 🌀": "⚡ BRAIN BLAST! 🌀", "Chefe derrotado! +500 🏆": "Boss defeated! +500 🏆",
    "🛡️ Escudo!": "🛡️ Shield!", "⚡ Tiro triplo!": "⚡ Triple shot!", "❤️ +1 vida!": "❤️ +1 life!", "🌀 Energia!": "🌀 Energy!",
    "🌀 ENTER!": "🌀 ENTER!", "VAI! 🚀": "GO! 🚀", "⏸️ Pausa (P para voltar)": "⏸️ Paused (P to resume)",
    "Fim de jogo!": "Game over!", "🏆 Novo recorde!": "🏆 New record!", "Enter: jogar de novo · Esc: sair": "Enter: play again · Esc: quit",
    "Setas: pilotar · Espaço: atirar · Enter: especial · P: pausa · Esc: sair": "Arrows: fly · Space: shoot · Enter: special · P: pause · Esc: quit", "🔧 Consertos": "🔧 Repairs", "🔧 Mecânico genial": "🔧 Genius mechanic",
    "Hora da manutenção! 🔧": "Maintenance time! 🔧", "Esse foguete precisa de uns ajustes... 🔧": "This rocket needs some tweaks... 🔧",
    "Vou turbinar esse motor! 🔧⚡": "I'm gonna boost this engine! 🔧⚡", "Foguete novinho em folha! 🔧✨": "Good as new! 🔧✨",
    "Pronto! Agora vai voar mais rápido! 🚀": "Done! Now it'll fly faster! 🚀", "Neutron, você é um gênio! 😎🔧": "Neutron, you're a genius! 😎🔧",
    "🎾 Brincar de bolinha com o Goddard": "🎾 Play ball with Goddard", "📝 Novo lembrete...": "📝 New reminder...",
    "📝 Novo lembrete": "📝 New reminder", "📋 Próximos lembretes": "📋 Upcoming reminders", "(nenhum para hoje)": "(none today)",
    "⚙️ Ver todos": "⚙️ See all", "🎮 Brincar": "🎮 Play", "🚀 Decolar agora": "🚀 Take off now", "💃 Dançar": "💃 Dance",
    "🧪 Inventar algo": "🧪 Invent something", "🐶 Goddard": "🐶 Goddard", "🗒️ Nota rápida...": "🗒️ Quick note...",
    "🗒️ Nota rápida": "🗒️ Quick note", "O que eu anoto?": "What should I write down?",
    "🎲 Decida por mim...": "🎲 Decide for me...", "🎲 Decida por mim": "🎲 Decide for me",
    "Opções separadas por vírgula:": "Options separated by commas:", "💧 Bebi água!": "💧 I drank water!",
    "Vai buscar, Goddard! 🎾": "Go fetch, Goddard! 🎾", "Mais longe agora! 💪": "Farther now! 💪",
    "Laaaaá longe! 🚀": "Waaaay over there! 🚀", "Essa foi longe! 😄": "That one went far! 😄", "Última! Vai! 🎾": "Last one! Go! 🎾",
    "Ufa, cansei! Boa, Goddard! 🐕": "Phew, I'm tired! Good boy, Goddard! 🐕", "Guardei a nota! 🗒️ Fica em Configurações → 📝 Meus.": "Note saved! 🗒️ It's in Settings → 📝 Mine.",
    "🗑️ Apagar nota": "🗑️ Delete note", "(nenhuma nota ainda)": "(no notes yet)",
    "🗒️ Notas rápidas (clique no Jimmy → Nota rápida):": "🗒️ Quick notes (click Jimmy → Quick note):",
    "💧 Hidratado de verdade": "💧 Truly hydrated",
    "Psiu! Já conhece o canal @oevetech no YouTube? ▶️ Clica em mim!": "Psst! Do you know the @oevetech channel on YouTube? ▶️ Click me!",
    "Quem me trouxe pro seu PC foi o @oevetech! Dá uma passada lá ▶️": "@oevetech brought me to your PC! Go check it out ▶️",
    "Ideia genial: se inscrever no @oevetech! 💡▶️": "Genius idea: subscribe to @oevetech! 💡▶️",
    "O Goddard aprovou o canal @oevetech! 🐕 Clica em mim pra ver ▶️": "Goddard approves the @oevetech channel! 🐕 Click me to see ▶️",
    "Tem vídeo novo de tecnologia no @oevetech? Vamos ver! ▶️": "Any new tech video on @oevetech? Let's see! ▶️",
    "📺 O Jimmy lembra do canal @oevetech (1 vez a cada 12–36 h)": "📺 Jimmy mentions the @oevetech channel (once every 12–36 h)", "🖱️ Cadê meu mouse?": "🖱️ Where's my mouse?", "Vento de novo?! 🌬️": "Wind again?! 🌬️", "🛸 Passeio": "🛸 Joyride", "🛸 Passeios": "🛸 Joyrides",
    "Que passeio! 😎": "What a ride! 😎",
    # --- menus ---
    "🍅 Pomodoro": "🍅 Pomodoro", "🔕 Não perturbe por 1 hora": "🔕 Do not disturb for 1 hour", "🚀 Lançar agora": "🚀 Launch now",
    "👫 Chamar um amigo": "👫 Call a friend", "🎾 Bolinha (jogar / guardar)": "🎾 Ball (throw / put away)",
    "🔄 Atualizar": "🔄 Update", "⚙️ Configurações": "⚙️ Settings", "🔄 Atualizar Pets": "🔄 Reload pets", "❌ Sair": "❌ Quit",
    "⏱️ Me avise em...": "⏱️ Remind me in...", "Outro tempo...": "Other time...", "🚀 Lançar o foguete": "🚀 Launch the rocket",
    "🎾 Bolinha": "🎾 Ball", "🧪 Inventar algo": "🧪 Invent something", "🦙 Soltar as lhamas": "🦙 Release the llamas",
    "⚡ Brain Blast": "⚡ Brain Blast", "📡 Visitar outro PC": "📡 Visit another PC", "🍅 Foco": "🍅 Focus", "☕ Pausa": "☕ Break",
    # --- janela de configurações ---
    "Configurações - Jimmy Neutron Pet": "Settings - Jimmy Neutron Pet",
    "Geral": "General", "Sons": "Sounds", "Avisos": "Reminders", "📝 Meus": "📝 Mine", "Extras": "Extras", "Apps": "Apps",
    "Clima": "Weather", "Online": "Online", "Tamanho:": "Size:", "Foguete:": "Rocket:", "Viagens:": "Trips:", "até": "to",
    "Monitor:": "Monitor:", "Idioma:": "Language:", "Principal": "Main", "Todos (atravessar)": "All (walk across)",
    "Bem lento": "Very slow", "Médio": "Medium", "Normal": "Normal", "Rápido": "Fast",
    "Mostrar o Goddard": "Show Goddard", "Mostrar o botão 🚀 LANÇAR": "Show the 🚀 LAUNCH button",
    "Foguete aparece em lugar aleatório": "Rocket appears in a random spot", "Iniciar junto com o Windows": "Start with Windows",
    "Esconder em jogos/vídeos em tela cheia": "Hide during fullscreen games/videos",
    "Dormir à noite (22h às 6h) e cochilar": "Sleep at night (10pm to 6am) and take naps",
    "Ativar sons": "Enable sounds", "Jimmy (paraquedas, pouso)": "Jimmy (parachute, landing)",
    "Ronco (Jimmy dormindo)": "Snoring (Jimmy asleep)", "Goddard (latido, bip, jetpack)": "Goddard (bark, beep, jetpack)",
    "Foguete (decolagem, explosão)": "Rocket (liftoff, explosion)", "Volume:": "Volume:", "Saída:": "Output:",
    "▶ Testar": "▶ Test", "Padrão do Windows": "Windows default",
    "Ativar lembretes": "Enable reminders", "Tocar som nos avisos": "Play a sound with reminders",
    "💧 Água": "💧 Water", "😌 Pausa": "😌 Break", "🍎 Comer": "🍎 Eat", "💪 Exercício": "💪 Exercise",
    "💤 Hora de dormir (22h)": "💤 Bedtime (10pm)", "▶ Testar aviso": "▶ Test reminder",
    "🍅 Pomodoro: foco": "🍅 Pomodoro: focus", "pausa": "break", "🔋 Avisar bateria fraca (notebook)": "🔋 Low battery warning (laptop)",
    "a cada ": "every ", " min": " min", "após ": "after ",
    "Lembrete:": "Reminder:", "Quando:": "When:", "➕ Adicionar": "➕ Add", "🗑️ Remover": "🗑️ Remove",
    "ex.: Reunião com a equipe": "e.g.: Team meeting", "(nenhum lembrete ainda)": "(no reminders yet)",
    "Uma vez": "Once", "Todo dia": "Every day", "Dias úteis (seg–sex)": "Weekdays (Mon–Fri)",
    "Toda segunda": "Every Monday", "Toda terça": "Every Tuesday", "Toda quarta": "Every Wednesday",
    "Toda quinta": "Every Thursday", "Toda sexta": "Every Friday", "Todo sábado": "Every Saturday", "Todo domingo": "Every Sunday",
    "⚡ Brain Blast de vez em quando": "⚡ Brain Blast now and then", "😴 Cochilar quando eu sair do PC": "😴 Nap when I'm away from the PC",
    "🎉 Comemorar datas especiais": "🎉 Celebrate special dates", "🎂 Meu aniversário:": "🎂 My birthday:",
    "dia": "day", "mês": "month", "👫 Visitas dos amigos (Carl, Sheen, Libby, Cindy)": "👫 Friend visits (Carl, Sheen, Libby, Cindy)",
    "Testar:": "Test:", "🎉 Festa": "🎉 Party", "👫 Amigo": "👫 Friend",
    "💬 Frases ao passar o mouse no Jimmy": "💬 Phrases when hovering over Jimmy", "🌙 Tom de noite (escurece à noite)": "🌙 Night tint (darker at night)",
    "Configurações:": "Settings:", "💾 Exportar...": "💾 Export...", "📂 Importar...": "📂 Import...",
    "🧪 Invenções do Jimmy": "🧪 Jimmy's inventions", "🦙 Lhamas do Carl": "🦙 Carl's llamas", "🧪 Invenção": "🧪 Invention",
    "🦙 Lhamas": "🦙 Llamas", "💃 Dançar quando tocar música": "💃 Dance when music plays", "🔬 Curiosidades de ciência": "🔬 Science facts",
    "🔬 Testar": "🔬 Test", "🔤 Digitar \"neutron\" faz um Brain Blast (lê o teclado)": "🔤 Typing \"neutron\" triggers a Brain Blast (reads the keyboard)",
    "🎮 Comentar quando eu abrir estes programas": "🎮 Comment when I open these programs", "Programa:": "Program:", "Frase:": "Phrase:",
    "ex.: spotify.exe": "e.g.: spotify.exe", "ex.: Solta o som! 🎵": "e.g.: Turn up the music! 🎵", "Último programa usado: -": "Last program used: -",
    "🌦️ Avisar o clima de manhã": "🌦️ Tell me the weather in the morning", "Cidade:": "City:", "Buscar": "Search",
    "ex.: São Paulo": "e.g.: London", "☔ Mostrar chuva na tela quando estiver chovendo": "☔ Show rain on screen when it's raining",
    "☔ Testar chuva": "☔ Test rain", "🍂 Efeitos das estações (folhas, pétalas, neve)": "🍂 Season effects (leaves, petals, snow)",
    "🍂 Testar estação": "🍂 Test season", "Usa o Open-Meteo (gratuito, sem conta). Só o nome da cidade é enviado.": "Uses Open-Meteo (free, no account). Only the city name is sent.",
    "Buscando...": "Searching...", "📡 Visitar outros PCs da rede com o pet": "📡 Visit other PCs on the network that have the pet",
    "📡 Visitar agora": "📡 Visit now", "Na primeira vez o Windows pede para liberar no Firewall (rede privada).": "The first time, Windows asks to allow it in the Firewall (private network).",
    "GitHub:": "GitHub:", "🔎 Verificar atualizações automaticamente": "🔎 Check for updates automatically",
    "⬇️ Atualizar sozinho quando sair versão nova": "⬇️ Update automatically when a new version is out", "🔎 Procurar agora": "🔎 Check now",
    "⬇️ Atualizar": "⬇️ Update", "Rede desligada": "Network off", "nenhum ainda": "none yet", "Procurando...": "Checking...",
    "Informe o repositório (usuario/nome).": "Enter the repository (user/name).",
    "ainda não há versões publicadas no repositório": "no versions have been published in the repository yet",
    "Restaurar padrão": "Reset to defaults", "Fechar": "Close", "Desenvolvedor:": "Developer:",
    "Abrir o canal no YouTube": "Open the YouTube channel", "Português": "Português", "English": "English",
    # --- diálogos ---
    "Me avise em...": "Remind me in...", "Daqui a quantos minutos?": "In how many minutes?", "Mensagem (opcional):": "Message (optional):",
    "Exportar": "Export", "Importar": "Import", "Exportar configurações": "Export settings", "Importar configurações": "Import settings",
    "Configurações e conquistas salvas! 💾": "Settings and achievements saved! 💾", "Configurações importadas! 📂": "Settings imported! 📂",
    "Atualizar": "Update", "A atualização automática funciona só no .exe.": "Automatic updates only work in the .exe.",
    "Desinstalar": "Uninstall", "Desinstalar Jimmy Neutron Pet": "Uninstall Jimmy Neutron Pet",
    "Desinstalar o Jimmy Neutron Pet?": "Uninstall Jimmy Neutron Pet?", "Apagar também suas configurações e conquistas?": "Also delete your settings and achievements?",
    "O Jimmy Neutron Pet foi desinstalado. Até mais! 👋": "Jimmy Neutron Pet has been uninstalled. See you! 👋",
}

# Textos com partes variáveis: {} vira (.+?) e cada pedaço também é traduzido
MODELOS_EN = [
    ("🔬 {}", "🔬 {}"),
    ("Pontos: {}", "Score: {}"), ("Onda {}", "Wave {}"), ("🏆 Recorde: {}", "🏆 Record: {}"),
    ("Onda {}: METEORO CHEFE! ☄️", "Wave {}: BOSS METEOR! ☄️"), ("Onda {}: REI GOOBOT! 👑", "Wave {}: KING GOOBOT! 👑"), ("Onda {} completa! +{} 🎉", "Wave {} complete! +{} 🎉"),
    ("{} pontos · onda {}", "{} points · wave {}"), ("Fizemos {} pontos! 🕹️", "We scored {} points! 🕹️"),
    ("Fizemos {} pontos! 🕹️ 🏆 Recorde!", "We scored {} points! 🕹️ 🏆 Record!"),
    ("Anotado! 📝 Te lembro às {}.", "Got it! 📝 I'll remind you at {}."),
    ("⚡ Calculando... Escolhi: {}! 🎲", "⚡ Calculating... I pick: {}! 🎲"),
    ("💧 Boa! {} copo(s) de água hoje.", "💧 Nice! {} glass(es) of water today."),
    ("⏰ {} — {}", "⏰ {} — {}"), ("{} — {}", "{} — {}"),
    ("Você salvou o dia! {}/{} ☄️ Perfeito!", "You saved the day! {}/{} ☄️ Perfect!"),
    ("Boa! Você pegou {}/{} meteoros! ☄️", "Nice! You got {}/{} meteors! ☄️"),
    ("Ufa... só {}/{}. Na próxima a gente pega! ☄️", "Phew... only {}/{}. We'll get them next time! ☄️"),
    ("{} 🏆 Recorde!", "{} 🏆 New record!"),
    ("🎉 Chegou o dia: {}!", "🎉 The day is here: {}!"), ("⏳ Amanhã é o dia: {}! 🎉", "⏳ Tomorrow is the day: {}! 🎉"),
    ("⏳ Faltam {} dias para: {}!", "⏳ {} days left until: {}!"), ("faltam {} dias", "{} days left"),
    ("🗓️ {} — {} ({})", "🗓️ {} — {} ({})"), ("{}❓", "{}❓"), ("📝 {}", "📝 {}"), ("⏰ {} ({} min)", "⏰ {} ({} min)"),
    ("Hoje em {}: {} {}, {}° a {}°. Leve guarda-chuva! ☔", "Today in {}: {} {}, {}° to {}°. Take an umbrella! ☔"),
    ("Hoje em {}: {} {}, {}° a {}°.", "Today in {}: {} {}, {}° to {}°."),
    ("{}: agora {} {}, {}°  (hoje {}° a {}°)", "{}: now {} {}, {}°  (today {}° to {}°)"),
    ("Foco por {} min! 🍅", "Focus for {} min! 🍅"), ("Hora da pausa! ☕ Descansa {} min.", "Break time! ☕ Rest for {} min."),
    ("Beleza! Te aviso em {} min. ⏱️", "Okay! I'll remind you in {} min. ⏱️"),
    ("🔋 Bateria em {}%! Liga o carregador! ⚡", "🔋 Battery at {}%! Plug in the charger! ⚡"),
    ("🏆 Conquista: {}!", "🏆 Achievement: {}!"), ("🏆 {} de {} conquistas", "🏆 {} of {} achievements"),
    ("✅ {}", "✅ {}"), ("🔒 {}  ({}/{})", "🔒 {}  ({}/{})"),
    ("Tem versão nova! v{} 🎉 Clique em mim com o botão direito → Atualizar", "New version available! v{} 🎉 Right-click me → Update"),
    ("Atualizando para a v{}... ⏬", "Updating to v{}... ⏬"), ("⬇️ Atualizando para v{}...", "⬇️ Updating to v{}..."),
    ("🔄 Atualizar para v{}", "🔄 Update to v{}"), ("🎉 Versão nova disponível: v{}", "🎉 New version available: v{}"),
    ("✅ Você já tem a versão mais nova (v{}).", "✅ You already have the latest version (v{})."), ("Versão instalada: v{}", "Installed version: v{}"),
    ("⚠️ {}", "⚠️ {}"), ("Cidade \"{}\" não encontrada", "City \"{}\" not found"),
    ("Sem conexão com o serviço de clima ({})", "Can't reach the weather service ({})"),
    ("não consegui ver as versões ({})", "couldn't check the versions ({})"), ("o GitHub respondeu erro {}", "GitHub returned error {}"),
    ("falhou o download ({})", "the download failed ({})"),
    ("Oi! Vim do PC do {}! 👋", "Hi! I came from {}'s PC! 👋"), ("E aí! Sou o Jimmy do {}! 🛰️", "Hey! I'm the Jimmy from {}! 🛰️"),
    ("Vou visitar o PC do {}! 🛰️", "I'm going to visit {}'s PC! 🛰️"), ("Voltei! O PC do {} é legal! 😄", "I'm back! {}'s PC is cool! 😄"),
    ("PCs com o pet: {}", "PCs with the pet: {}"), ("Último programa usado: {}", "Last program used: {}"),
    ("{}: {} min (clique para parar)", "{}: {} min (click to stop)"), ("🍅 Pomodoro ({} min de foco)", "🍅 Pomodoro ({} min of focus)"),
    ("🔔 Reativar (silêncio até {})", "🔔 Turn back on (quiet until {})"), ("{} minutos", "{} minutes"),
    ("⏳ {}: faltam {} min", "⏳ {}: {} min left"), ("❌ Cancelar timers ({})", "❌ Cancel timers ({})"),
    ("⏰ {} · {} — {}", "⏰ {} · {} — {}"), ("{}  →  {}", "{}  →  {}"), ("Monitor {} ({}x{})", "Monitor {} ({}x{})"),
    ("Baixar e instalar a versão {}?\nO pet reabre sozinho.", "Download and install version {}?\nThe pet will reopen by itself."),
    ("Não deu para atualizar: {}", "Couldn't update: {}"), ("Não deu para trocar o arquivo:\n{}", "Couldn't replace the file:\n{}"),
    ("Não deu para salvar:\n{}", "Couldn't save:\n{}"), ("Não deu para ler o arquivo:\n{}", "Couldn't read the file:\n{}"),
]
_MODELOS_RX = None

def tr(t):
    """Traduz um texto para o idioma escolhido (português é o original)."""
    global _MODELOS_RX
    if CFG.get("idioma", "pt") != "en" or not isinstance(t, str) or not t:
        return t
    if t in EN:
        return EN[t]
    if _MODELOS_RX is None:
        _MODELOS_RX = [(re.compile("^" + re.escape(pt).replace(re.escape("{}"), "(.+?)") + "$", re.S), en)
                       for pt, en in sorted(MODELOS_EN, key=lambda m: -len(m[0]))]
    for rx, en in _MODELOS_RX:
        m = rx.match(t)
        if m:
            return en.format(*[tr(g) for g in m.groups()])
    return t

def traduzir_janela(w):
    """Traduz todos os textos de uma janela já montada."""
    from PyQt6.QtWidgets import QAbstractButton, QAbstractSpinBox
    w.setWindowTitle(tr(w.windowTitle()))
    for x in w.findChildren(QLabel): x.setText(tr(x.text())); x.setToolTip(tr(x.toolTip()))
    for x in w.findChildren(QAbstractButton): x.setText(tr(x.text()))
    for x in w.findChildren(QLineEdit): x.setPlaceholderText(tr(x.placeholderText()))
    for x in w.findChildren(QComboBox):
        for i in range(x.count()): x.setItemText(i, tr(x.itemText(i)))
    for x in w.findChildren(QSpinBox):
        x.setPrefix(tr(x.prefix())); x.setSuffix(tr(x.suffix())); x.setSpecialValueText(tr(x.specialValueText()))
    for x in w.findChildren(QTabWidget):
        for i in range(x.count()): x.setTabText(i, tr(x.tabText(i)))

class TLabel(QLabel):
    """Rótulo que se traduz sozinho (para textos que mudam com o tempo)."""
    def setText(self, t):
        super().setText(tr(t))

class TList(QListWidget):
    def addItem(self, t):
        super().addItem(tr(t) if isinstance(t, str) else t)

class TMenu(QMenu):
    """Menu que traduz os itens ao criar (e guarda o original para trocar de idioma)."""
    def addAction(self, *a):
        if a and isinstance(a[0], str):
            act = super().addAction(tr(a[0]), *a[1:])
            act.setProperty("pt", a[0])
            return act
        return super().addAction(*a)

    def addMenu(self, *a):
        if a and isinstance(a[0], str):
            sub = TMenu(tr(a[0]), self)
            super().addMenu(sub)
            sub.menuAction().setProperty("pt", a[0])
            return sub
        return super().addMenu(*a)

    def retraduzir(self):
        for act in self.actions():
            pt = act.property("pt")
            if pt: act.setText(tr(pt))

# ---------- Frases ao passar o mouse ----------
FRASES = ["Pensa, pensa, pensa! 🤔", "Goddard, analise! 🐕", "Bateria de cérebro carregada! 🔋",
          "A ciência resolve tudo! 🔬", "Gotta blast! 🚀", "Mais uma invenção vindo aí... 💡",
          "Não toque no foguete! 😅", "Precisa de ajuda? 🤓", "Meu QI é de 210! 🧠",
          "Cuidado: alto risco de explosão! 💥"]

# ---------- Clima (Open-Meteo, grátis e sem conta; envia só o nome da cidade) ----------
def clima_desc(code):
    if code == 0: return "☀️", "céu limpo"
    if code in (1, 2): return "🌤️", "poucas nuvens"
    if code == 3: return "☁️", "nublado"
    if code in (45, 48): return "🌫️", "neblina"
    if 51 <= code <= 57: return "🌦️", "garoa"
    if 61 <= code <= 67: return "🌧️", "chuva"
    if 71 <= code <= 77 or code in (85, 86): return "❄️", "neve"
    if 80 <= code <= 82: return "🌧️", "pancadas de chuva"
    if code >= 95: return "⛈️", "tempestade"
    return "🌡️", "tempo instável"

def chovendo(code):
    return 51 <= code <= 67 or 80 <= code <= 82 or code >= 95

def texto_clima(d):
    emoji, desc = clima_desc(d["codigo"])
    t = f"Hoje em {d['nome']}: {emoji} {desc}, {round(d['min'])}° a {round(d['max'])}°."
    if d["chuva"] >= 50 or chovendo(d["codigo"]):
        t += " Leve guarda-chuva! ☔"
    return t

class ClimaWorker(QObject):
    pronto = pyqtSignal(object)

    def buscar(self, cidade):
        threading.Thread(target=self._run, args=(cidade,), daemon=True).start()

    def _run(self, cidade):
        try:
            q = urllib.parse.urlencode({"name": cidade, "count": 1, "language": "pt", "format": "json"})
            with urllib.request.urlopen("https://geocoding-api.open-meteo.com/v1/search?" + q, timeout=10) as r:
                geo = json.load(r)
            if not geo.get("results"):
                self.pronto.emit({"erro": f"Cidade \"{cidade}\" não encontrada"})
                return
            g = geo["results"][0]
            q = urllib.parse.urlencode({
                "latitude": g["latitude"], "longitude": g["longitude"], "current_weather": "true",
                "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto", "forecast_days": 1})
            with urllib.request.urlopen("https://api.open-meteo.com/v1/forecast?" + q, timeout=10) as r:
                f = json.load(r)
            d = f["daily"]
            self.pronto.emit({"nome": g["name"], "agora": f["current_weather"]["weathercode"],
                              "temp": f["current_weather"]["temperature"], "codigo": d["weathercode"][0],
                              "max": d["temperature_2m_max"][0], "min": d["temperature_2m_min"][0],
                              "chuva": (d.get("precipitation_probability_max") or [0])[0] or 0})
        except Exception as e:
            self.pronto.emit({"erro": f"Sem conexão com o serviço de clima ({type(e).__name__})"})

# ---------- Música tocando? (medidor de pico da saída de som padrão, via Core Audio) ----------
import uuid

class _GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16), ("Data3", ctypes.c_uint16),
                ("Data4", ctypes.c_ubyte * 8)]

def _guid(texto):
    return _GUID.from_buffer_copy(uuid.UUID(texto).bytes_le)

_CLSID_ENUM = _guid("BCDE0395-E52F-467C-8E3D-C4579291692E")
_IID_ENUM = _guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
_IID_METER = _guid("C02216F6-8C67-4B5B-9D00-D008E73E0064")

def _com(ptr, indice, argtypes, *args, restype=ctypes.HRESULT):
    """Chama o método número `indice` da tabela virtual de uma interface COM."""
    vtbl = ctypes.cast(ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return proto(vtbl[indice])(ptr, *args)

class MedidorSom:
    """Pico do som que está saindo pela saída padrão (0 = silêncio, 1 = máximo)."""
    def __init__(self):
        self.meter = None
        self.aberto_em = 0.0

    def _soltar(self):
        if self.meter:
            try: _com(self.meter, 2, [], restype=ctypes.c_ulong)
            except OSError: pass
        self.meter = None

    def _abrir(self):
        self._soltar()
        ctypes.windll.ole32.CoInitializeEx(None, 2)
        enum = ctypes.c_void_p()
        ctypes.oledll.ole32.CoCreateInstance(ctypes.byref(_CLSID_ENUM), None, 23, ctypes.byref(_IID_ENUM), ctypes.byref(enum))
        dev = ctypes.c_void_p()
        _com(enum, 4, [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)], 0, 1, ctypes.byref(dev))
        meter = ctypes.c_void_p()
        _com(dev, 3, [ctypes.POINTER(_GUID), wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)],
             ctypes.byref(_IID_METER), 23, None, ctypes.byref(meter))
        _com(dev, 2, [], restype=ctypes.c_ulong)
        _com(enum, 2, [], restype=ctypes.c_ulong)
        self.meter = meter
        self.aberto_em = time.time()

    def pico(self):
        try:
            if self.meter is None or time.time() - self.aberto_em > 60:   # segue troca de saída de som
                self._abrir()
            v = ctypes.c_float()
            _com(self.meter, 3, [ctypes.POINTER(ctypes.c_float)], ctypes.byref(v))
            return v.value
        except OSError:
            self.meter = None
            return 0.0

# ---------- Atualização pelo GitHub Releases ----------
class Atualizador(QObject):
    resultado = pyqtSignal(object)
    baixado = pyqtSignal(object)

    def verificar(self, repo):
        threading.Thread(target=self._verificar, args=(repo,), daemon=True).start()

    def _verificar(self, repo):
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/latest",
                                         headers={"User-Agent": "JimmyNeutronPet", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.load(r)
            url = next((a["browser_download_url"] for a in d.get("assets", [])
                        if a.get("name", "").lower() == "jimmyneutronpet.exe"), None)
            self.resultado.emit({"versao": str(d.get("tag_name", "")).lstrip("vV"), "url": url})
        except urllib.error.HTTPError as e:
            msg = "ainda não há versões publicadas no repositório" if e.code == 404 else f"o GitHub respondeu erro {e.code}"
            self.resultado.emit({"erro": msg})
        except Exception as e:
            self.resultado.emit({"erro": f"não consegui ver as versões ({type(e).__name__})"})

    def baixar(self, url, destino):
        threading.Thread(target=self._baixar, args=(url, destino), daemon=True).start()

    def _baixar(self, url, destino):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JimmyNeutronPet"})
            with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
                shutil.copyfileobj(r, f)
            self.baixado.emit({"arquivo": destino})
        except Exception as e:
            self.baixado.emit({"erro": f"falhou o download ({type(e).__name__})"})

# ---------- Rede local: o Jimmy visita outros PCs com o pet ----------
class Rede(QObject):
    """Mensagens pequenas em UDP broadcast na rede local (porta 47123). Só fala com outros pets."""
    PORTA = 47123
    PORTA_DESTINO = 47123
    BIND = QHostAddress.SpecialAddress.AnyIPv4
    DESTINO = QHostAddress.SpecialAddress.Broadcast

    def __init__(self, on_msg):
        super().__init__()
        import uuid as _uuid
        self.id = _uuid.uuid4().hex[:12]
        self.nome = socket.gethostname()
        self.on_msg = on_msg
        self.peers = {}
        self.sock = QUdpSocket(self)
        self.sock.bind(QHostAddress(self.BIND), self.PORTA,
                       QUdpSocket.BindFlag.ShareAddress | QUdpSocket.BindFlag.ReuseAddressHint)
        self.sock.readyRead.connect(self._ler)

    def enviar(self, msg):
        msg = dict(msg, de=self.id, nome=self.nome, app="jimmypet")
        self.sock.writeDatagram(json.dumps(msg).encode("utf-8"),
                                QHostAddress(self.DESTINO), self.PORTA_DESTINO)

    def anunciar(self):
        self.enviar({"tipo": "oi"})

    def _ler(self):
        while self.sock.hasPendingDatagrams():
            dg = self.sock.receiveDatagram()
            try:
                msg = json.loads(bytes(dg.data()).decode("utf-8"))
            except ValueError:
                continue
            if not isinstance(msg, dict) or msg.get("app") != "jimmypet" or msg.get("de") == self.id:
                continue
            self.peers[msg["de"]] = {"nome": str(msg.get("nome", "?"))[:40], "visto": time.time()}
            if msg.get("para") in (None, self.id):
                self.on_msg(msg)

    def vivos(self):
        return {k: v for k, v in self.peers.items() if time.time() - v["visto"] < 40}

    def fechar(self):
        self.sock.close()

# ---------- Easter egg: digitar "neutron" (só guarda as últimas 7 letras, na memória) ----------
class _KBD(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD), ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

_HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

class TecladoNeutron:
    def __init__(self, on_neutron):
        self.on_neutron = on_neutron
        self.buf = ""
        self.hook = None
        self.proc = _HOOKPROC(self._cb)
        u = ctypes.windll.user32
        u.SetWindowsHookExW.argtypes = [ctypes.c_int, _HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        u.SetWindowsHookExW.restype = ctypes.c_void_p
        u.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        u.CallNextHookEx.restype = ctypes.c_ssize_t
        u.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.GetModuleHandleW.restype = wintypes.HMODULE

    def ligar(self):
        if not self.hook:
            self.hook = ctypes.windll.user32.SetWindowsHookExW(13, self.proc, ctypes.windll.kernel32.GetModuleHandleW(None), 0)

    def desligar(self):
        if self.hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook)
            self.hook = None
        self.buf = ""

    def tecla(self, vk):
        if 0x41 <= vk <= 0x5A:
            self.buf = (self.buf + chr(vk).lower())[-7:]
            if self.buf == "neutron":
                self.buf = ""
                QTimer.singleShot(0, self.on_neutron)
        else:
            self.buf = ""

    def _cb(self, code, wparam, lparam):
        if code == 0 and wparam in (0x100, 0x104):
            self.tecla(ctypes.cast(lparam, ctypes.POINTER(_KBD)).contents.vkCode)
        return ctypes.windll.user32.CallNextHookEx(None, code, wparam, lparam)

# ---------- Bateria (notebook) ----------
class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                ("BatteryLifeTime", wintypes.DWORD), ("BatteryFullLifeTime", wintypes.DWORD)]

def bateria():
    """(porcentagem, na tomada) ou None se não houver bateria (PC de mesa)."""
    sps = SYSTEM_POWER_STATUS()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)): return None
    if sps.BatteryFlag & 128 or sps.BatteryLifePercent == 255: return None
    return sps.BatteryLifePercent, sps.ACLineStatus == 1
# Tamanho geral dos pets: 1.0 = Jimmy com ~144 px de altura. Muda tudo junto, na mesma proporção.
ESCALA = CFG["tamanho"] / 100

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "JimmyNeutronPet"

def autostart_cmd():
    # No .exe abre o próprio executável; rodando o .py usa o pythonw (sem janela de console)
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return f'"{pythonw}" "{os.path.abspath(sys.argv[0])}"'

def autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
        return True
    except OSError:
        return False

def set_autostart(on):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if on:
                winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ, autostart_cmd())
            else:
                try:
                    winreg.DeleteValue(k, RUN_NAME)
                except FileNotFoundError:
                    pass
    except OSError as e:
        log_error(e)

class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

_user32 = ctypes.windll.user32
_user32.GetForegroundWindow.restype = wintypes.HWND
_user32.MonitorFromWindow.restype = wintypes.HMONITOR
_user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]

def foreground_is_fullscreen():
    """Janela da frente (de outro programa) ocupando o monitor inteiro: jogo, vídeo, apresentação."""
    hwnd = _user32.GetForegroundWindow()
    if not hwnd: return False
    pid = wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == os.getpid(): return False
    cls = ctypes.create_unicode_buffer(256)
    _user32.GetClassNameW(hwnd, cls, 256)
    if cls.value in ("Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"): return False  # área de trabalho
    rect = wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if not _user32.GetMonitorInfoW(_user32.MonitorFromWindow(hwnd, 2), ctypes.byref(mi)): return False
    m = mi.rcMonitor
    return rect.left <= m.left and rect.top <= m.top and rect.right >= m.right and rect.bottom >= m.bottom

SOM_DIR = os.path.join(RES_DIR, "sons")

class Sons:
    """Efeitos sonoros (WAV na pasta sons, embutida no .exe)."""
    NOMES = ("explosao", "decolagem", "paraquedas", "pouso", "goddard", "latido", "jetpack_liga", "jetpack", "ronco", "aviso",
             "brainblast", "fogos", "bolinha", "laser", "estouro")
    LOOPS = ("jetpack", "ronco")
    # Cada som pertence a um personagem (dá para desligar por grupo nas configurações)
    GRUPO = {"paraquedas": "som_jimmy", "pouso": "som_jimmy", "ronco": "som_ronco", "aviso": "som_avisos",
             "latido": "som_goddard", "goddard": "som_goddard", "jetpack_liga": "som_goddard", "jetpack": "som_goddard",
             "decolagem": "som_foguete", "explosao": "som_foguete",
             "brainblast": "som_jimmy", "fogos": "som_jimmy", "bolinha": "som_goddard", "laser": "som_jimmy", "estouro": "som_foguete"}

    def liberado(self, nome):
        return CFG["sons"] and not nao_perturbe() and CFG.get(self.GRUPO.get(nome, ""), True)

    def __init__(self):
        self.efeitos = {}
        self.saida_id = None
        self.carregar()
        # Trocou fone/caixa/monitor ou a saída padrão do Windows: recria os sons na saída nova
        self.dispositivos = QMediaDevices()
        self.dispositivos.audioOutputsChanged.connect(self.verificar_saida)

    def saida_desejada(self):
        device = QMediaDevices.defaultAudioOutput()
        for d in QMediaDevices.audioOutputs():
            if CFG["saida_som"] and d.description() == CFG["saida_som"]:
                device = d
        return device

    def verificar_saida(self):
        """Chamado quando os dispositivos mudam e a cada minuto (o Windows nem sempre avisa)."""
        novo = bytes(self.saida_desejada().id())
        if novo != self.saida_id:
            self.saida_id = novo
            self.carregar()

    def carregar(self):
        tocando = [n for n in self.LOOPS if n in self.efeitos and self.efeitos[n].isPlaying()]
        for fx in self.efeitos.values():
            fx.stop(); fx.deleteLater()
        self.efeitos = {}
        for nome in self.NOMES:
            path = os.path.join(SOM_DIR, nome + ".wav")
            if os.path.exists(path):
                fx = QSoundEffect()
                # Erro ao carregar/tocar vai para o log (senão o som falha calado)
                fx.statusChanged.connect(lambda fx=fx, nome=nome: fx.status() == QSoundEffect.Status.Error
                                         and log_error(RuntimeError(f"som '{nome}' com erro em {fx.audioDevice().description()}")))
                fx.setSource(QUrl.fromLocalFile(path))
                if nome in self.LOOPS:
                    fx.setLoopCount(QSoundEffect.Loop.Infinite.value)
                self.efeitos[nome] = fx
        self.aplicar_cfg()
        for n in tocando: self.efeitos[n].play()

    def aplicar_cfg(self):
        device = self.saida_desejada()
        if self.saida_id is not None and bytes(device.id()) != self.saida_id and self.efeitos:
            self.saida_id = bytes(device.id())
            self.carregar()   # mudou a saída nas configurações: recria (setAudioDevice depois de carregar não pega)
            return
        self.saida_id = bytes(device.id())
        for fx in self.efeitos.values():
            fx.setAudioDevice(device)
            fx.setVolume(max(0, min(100, CFG["volume"])) / 100)

    def tocando_algo(self):
        """O próprio pet está fazendo barulho (efeito recente ou loop)?"""
        if time.time() - getattr(self, "ultimo_som", 0) < 3: return True
        return any(self.efeitos[n].isPlaying() for n in self.LOOPS if n in self.efeitos)

    def loop(self, nome, ligado):
        """Liga/desliga um som contínuo (pode chamar todo quadro)."""
        fx = self.efeitos.get(nome)
        if not fx: return
        ligado = ligado and self.liberado(nome)
        if ligado and not fx.isPlaying():
            fx.play()
        elif not ligado and fx.isPlaying():
            fx.stop()

    def tocar(self, nome, forcar=False):
        fx = self.efeitos.get(nome)
        self.ultimo_som = time.time()
        if fx and (self.liberado(nome) or forcar):
            if fx.status() == QSoundEffect.Status.Error:
                self.carregar()   # a saída sumiu (suspensão, fone desconectado): tenta de novo
                fx = self.efeitos.get(nome)
            fx.play()

SONS = None

def tocar(nome):
    if SONS: SONS.tocar(nome)

def som_loop(nome, ligado):
    if SONS: SONS.loop(nome, ligado)

def vel():
    """Fator das velocidades no chão: pet menor anda menos pixels (as velocidades foram ajustadas em 75%)."""
    return ESCALA / 0.75

def _overlay_flags(widget):
    # Janela só de enfeite: sem borda, por cima, sem foco e o clique passa direto
    widget.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint |
                          Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

def _topmost(widget):
    if not widget.isVisible(): return
    try:
        ctypes.windll.user32.SetWindowPos(int(widget.winId()), -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
    except (AttributeError, OSError):
        widget.raise_()

class Shadow(QWidget):
    """Sombra no chão embaixo de um pet."""
    def __init__(self):
        super().__init__()
        _overlay_flags(self)
        self.alpha = 0.3

    def place(self, cx, cy, w, h, alpha):
        w, h = max(4, int(w)), max(2, int(h))
        self.setGeometry(int(cx - w / 2) + OX, int(cy - h / 2) + OY, w, h)
        self.alpha = alpha
        if not self.isVisible(): self.show()
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        g = QRadialGradient(r.width() / 2, r.height() / 2, r.width() / 2)
        g.setColorAt(0.0, QColor(0, 0, 0, int(255 * self.alpha)))
        g.setColorAt(0.6, QColor(0, 0, 0, int(255 * self.alpha * 0.6)))
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(g)
        # Gradiente circular achatado na elipse
        p.scale(1, r.height() / max(1, r.width()))
        p.drawEllipse(0, 0, r.width(), r.width())

class Effects(QWidget):
    """Fumaça e faíscas. A janela cobre só a área das partículas e some quando não há nenhuma."""
    def __init__(self):
        super().__init__()
        _overlay_flags(self)
        self.parts = []
        self.ox = self.oy = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)

    def _add(self, **kw):
        self.parts.append(kw)
        if not self.timer.isActive(): self.timer.start(30)

    def smoke(self, x, y, size, life=40, vx=0.0, vy=0.0, gray=200, alpha=0.45, grow=1.6):
        k = vel()
        self._add(kind="smoke", x=x, y=y, vx=vx * k, vy=vy * k, r=size * k, grow=grow, age=0, life=life,
                  gray=gray, alpha=alpha)

    def sparks(self, x, y, n, colors=None, speed=(2, 9), life=(22, 45), gravity=1.0):
        k = vel()
        colors = colors or [(255, 230, 120), (255, 170, 40), (255, 110, 30), (255, 255, 200)]
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(*speed) * k
            self._add(kind="spark", x=x, y=y, vx=math.cos(a) * sp, vy=math.sin(a) * sp - 2 * k * gravity,
                      r=random.uniform(1.5, 3.5) * k, age=0, life=random.randint(*life),
                      color=random.choice(colors), g=gravity)

    def confetti(self, x0, x1, y, n, colors):
        k = vel()
        for _ in range(n):
            self._add(kind="confetti", x=random.uniform(x0, x1), y=y + random.uniform(-40, 10),
                      vx=random.uniform(-1.5, 1.5) * k, vy=random.uniform(0.5, 2.5) * k,
                      r=random.uniform(3, 5) * k, age=0, life=random.randint(130, 190),
                      rot=random.uniform(0, 360), vrot=random.uniform(-12, 12),
                      phase=random.uniform(0, 6.28), color=random.choice(colors))

    def folhas(self, x0, x1, y, n, colors):
        k = vel()
        for _ in range(n):
            self._add(kind="confetti", forma="folha", x=random.uniform(x0, x1), y=y + random.uniform(-30, 10),
                      vx=random.uniform(-1, 1) * k, vy=random.uniform(0.4, 1.1) * k,
                      r=random.uniform(4, 6.5) * k, age=0, life=random.randint(220, 300),
                      rot=random.uniform(0, 360), vrot=random.uniform(-5, 5),
                      phase=random.uniform(0, 6.28), color=random.choice(colors))

    def bolhas(self, x, y, n):
        k = vel()
        for _ in range(n):
            self._add(kind="bolha", x=x + random.uniform(-30, 30) * k, y=y + random.uniform(-15, 15) * k,
                      vx=random.uniform(-0.4, 0.4) * k, vy=-random.uniform(0.4, 1.4) * k, r=random.uniform(3, 7) * k,
                      age=0, life=random.randint(45, 80), phase=random.uniform(0, 6.28))

    def snow(self, x0, x1, y, n):
        k = vel()
        for _ in range(n):
            self._add(kind="snow", x=random.uniform(x0, x1), y=y + random.uniform(-30, 10),
                      vx=0.0, vy=random.uniform(0.6, 1.6) * k, r=random.uniform(1.5, 3.5) * k,
                      age=0, life=random.randint(180, 260), phase=random.uniform(0, 6.28), color=(255, 255, 255))

    def rain(self, x0, x1, n, chao):
        k = vel()
        for _ in range(n):
            y = random.uniform(-20, 40)
            vy = random.uniform(14, 18) * k
            self._add(kind="rain", x=random.uniform(x0, x1), y=y, vx=-1.5 * k, vy=vy,
                      r=random.uniform(6, 10) * k, age=0, life=max(5, int((chao - y) / vy)))

    def clear(self):
        self.parts = []
        self.timer.stop()
        self.hide()

    def step(self):
        alive = []
        for p in self.parts:
            p["age"] += 1
            if p["age"] >= p["life"]: continue
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["kind"] == "spark":
                p["vy"] += 0.25 * vel() * p.get("g", 1.0)   # gravidade
                p["vx"] *= 0.98
            elif p["kind"] == "rain":
                pass   # chuva cai reta, sem gravidade extra
            elif p["kind"] == "bolha":
                p["x"] += math.sin(p["age"] * 0.2 + p["phase"]) * 0.5
            elif p["kind"] in ("confetti", "snow"):
                # Cai balançando de um lado para o outro
                p["vy"] = min(p["vy"] + 0.03 * vel(), 2.5 * vel())
                p["x"] += math.sin(p["age"] * 0.08 + p["phase"]) * 0.9 * vel()
                p["vx"] *= 0.97
                if p["kind"] == "confetti": p["rot"] += p["vrot"]
            else:
                p["vx"] *= 0.96
                p["vy"] = p["vy"] * 0.96 - 0.03 * vel()   # fumaça sobe devagar
            alive.append(p)
        self.parts = alive
        if not alive:
            self.clear()
            return
        # Janela do tamanho exato da nuvem de partículas
        pad = 4
        x0 = min(p["x"] - self.radius(p) for p in alive) - pad
        y0 = min(p["y"] - self.radius(p) for p in alive) - pad
        x1 = max(p["x"] + self.radius(p) for p in alive) + pad
        y1 = max(p["y"] + self.radius(p) for p in alive) + pad
        self.ox, self.oy = int(x0), int(y0)
        self.setGeometry(self.ox + OX, self.oy + OY, max(2, int(x1 - x0)), max(2, int(y1 - y0)))
        if not self.isVisible(): self.show()
        self.update()

    @staticmethod
    def radius(p):
        if p["kind"] in ("confetti", "snow"): return p["r"] * 1.5
        if p["kind"] == "rain": return p["r"] * 2
        t = p["age"] / p["life"]
        return p["r"] * (1 + p.get("grow", 0) * t)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for q in self.parts:
            t = q["age"] / q["life"]
            r = self.radius(q)
            cx, cy = q["x"] - self.ox, q["y"] - self.oy
            if q["kind"] == "bolha":
                a = int(200 * (1 - t))
                p.setPen(QPen(QColor(255, 255, 255, a), 1))
                p.setBrush(QColor(190, 225, 255, a // 3))
                p.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))
                p.setPen(Qt.PenStyle.NoPen)
                continue
            if q["kind"] == "rain":
                p.setPen(QPen(QColor(180, 210, 255, 170), 1.5))
                p.drawLine(int(cx), int(cy), int(cx - q["vx"]), int(cy - q["r"] * 1.6))
                p.setPen(Qt.PenStyle.NoPen)
                continue
            if q["kind"] == "smoke":
                a = int(255 * q["alpha"] * (1 - t))
                g = QRadialGradient(cx, cy, r)
                g.setColorAt(0, QColor(q["gray"], q["gray"], q["gray"], a))
                g.setColorAt(1, QColor(q["gray"], q["gray"], q["gray"], 0))
                p.setBrush(g)
            elif q["kind"] == "confetti":
                cr, cg, cb = q["color"]
                p.setBrush(QColor(cr, cg, cb, int(255 * min(1, (1 - t) * 4))))
                p.save()
                p.translate(cx, cy)
                p.rotate(q["rot"])
                if q.get("forma") == "folha":
                    p.drawEllipse(int(-q["r"]), int(-q["r"] * 0.45), int(2 * q["r"]), int(0.9 * q["r"]))
                else:
                    p.drawRect(int(-q["r"]), int(-q["r"] * 0.6), int(2 * q["r"]), int(1.2 * q["r"]))
                p.restore()
                continue
            else:
                cr, cg, cb = q["color"]
                fade_out = (1 - t * t) if q["kind"] == "spark" else min(1, (1 - t) * 4)
                p.setBrush(QColor(cr, cg, cb, int(255 * fade_out)))
            p.drawEllipse(int(cx - r), int(cy - r), int(2 * r), int(2 * r))

FX = None

class Ball(QWidget):
    """Bolinha de tênis: arraste e jogue; o Goddard busca."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        geo = tela_geo()
        self.sw, self.sh = geo.width(), geo.height()
        self.held_by = None
        self.dragging = False
        self.thrown = False
        self.bx = self.by = 0.0
        self.vx = self.vy = 0.0
        self.r = 10
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)

    @property
    def ground(self):
        return self.sh - 10 - self.r

    def spawn(self):
        # Cai do topo da tela. Às vezes vem arremessada para um canto e ricocheteia
        # nas laterais e no teto antes de cair de vez.
        k = vel()
        self.r = max(5, int(11 * k))
        self.by = self.r + 2
        if random.random() < 0.5:
            self.bx = random.uniform(self.sw * 0.15, self.sw * 0.85)
            self.vx = random.uniform(-3, 3) * k
            self.vy = 0.0
            self.bouncy = 0
        else:
            lado = random.choice([-1, 1])
            self.bx = self.sw / 2 + random.uniform(-150, 150)
            self.vx = lado * random.uniform(20, 30) * k
            self.vy = random.uniform(-6, 4) * k
            self.bouncy = random.randint(3, 6)   # quantas batidas "elásticas" antes de cansar
        self.held_by = None
        self.thrown = True
        self.place()
        self.show()
        self.timer.start(30)

    def arremessar(self, x, y, vx, vy):
        """O Jimmy joga a bolinha da mão dele."""
        self.r = max(5, int(11 * vel()))
        self.bx, self.by, self.vx, self.vy = x, y, vx, vy
        self.bouncy = 0
        self.held_by = None
        self.thrown = True
        self.place()
        self.show()
        self.timer.start(30)

    def put_away(self):
        self.timer.stop()
        self.held_by = None
        self.thrown = False
        self.hide()

    def step(self):
        k = vel()
        if self.held_by is not None:
            # Na boca do Goddard
            g = self.held_by
            self.bx = g.x + g.box * (0.86 if g.direction == 1 else 0.14)
            self.by = g.y + g.box * 0.62
        elif not self.dragging:
            self.vy += 0.6 * k
            self.bx += self.vx
            self.by += self.vy
            if self.by >= self.ground:
                self.by = self.ground
                if self.vy > 3 * k:
                    if self.vy > 6 * k: tocar("bolinha")
                    self.vy = -self.vy * 0.55   # quica
                else:
                    self.vy = 0.0
                self.vx *= 0.9                  # atrito no chão
            else:
                self.vx *= 0.995
            elastico = getattr(self, "bouncy", 0) > 0
            if self.bx < self.r or self.bx > self.sw - self.r:
                self.bx = max(self.r, min(self.bx, self.sw - self.r))
                # bate na lateral: nas primeiras batidas do ricochete quase não perde força
                self.vx = -self.vx * (0.9 if elastico else 0.6)
                if elastico:
                    self.vy -= random.uniform(6, 12) * k   # joga para o teto
                    self.bouncy -= 1
                if abs(self.vx) > 4 * k: tocar("bolinha")
            if self.by < self.r:
                self.by = self.r
                self.vy = abs(self.vy) * (0.85 if elastico else 0.5)   # bate no teto
                if elastico: self.bouncy -= 1
                if abs(self.vy) > 4 * k: tocar("bolinha")
        self.place()

    def place(self):
        s = self.r * 2 + 4
        self.setGeometry(int(self.bx - self.r - 2) + OX, int(self.by - self.r - 2) + OY, s, s)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.r
        g = QRadialGradient(r * 0.7, r * 0.7, r * 1.6)
        g.setColorAt(0, QColor(240, 255, 120))
        g.setColorAt(1, QColor(150, 190, 20))
        p.setPen(QColor(90, 120, 10))
        p.setBrush(g)
        p.drawEllipse(2, 2, 2 * r, 2 * r)
        # Costura branca da bolinha de tênis
        p.setPen(QColor(255, 255, 255, 220))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(int(2 - r * 0.9), 2, 2 * r, 2 * r, -60 * 16, 120 * 16)
        p.drawArc(int(2 + r * 0.9), 2, 2 * r, 2 * r, 120 * 16, 120 * 16)

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        self.held_by = None   # pode tirar da boca do Goddard
        self.dragging = True
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        gp = e.globalPosition()
        self.last = (gp.x(), gp.y())
        self.vx = self.vy = 0.0

    def mouseMoveEvent(self, e):
        if not self.dragging: return
        gp = e.globalPosition()
        dx, dy = gp.x() - self.last[0], gp.y() - self.last[1]
        self.last = (gp.x(), gp.y())
        self.bx += dx
        self.by = min(self.by + dy, self.ground)
        self.vx = self.vx * 0.5 + dx * 0.5
        self.vy = self.vy * 0.5 + dy * 0.5
        self.place()

    def mouseReleaseEvent(self, e):
        if not self.dragging: return
        self.dragging = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        lim = 25 * vel()
        self.vx = max(-lim, min(lim, self.vx))
        self.vy = max(-lim, min(lim, self.vy))
        self.thrown = True   # Goddard vai buscar

BALL = None

def desenhar_meteoro(p, cx, cy, r, giro, vx, vy):
    """Pedra em chamas com crateras; o rastro de fogo fica do lado contrário ao movimento."""
    ang = math.atan2(vy, vx)
    tx, ty = cx - math.cos(ang) * r * 1.4, cy - math.sin(ang) * r * 1.4
    g = QRadialGradient(tx, ty, r * 1.6)
    g.setColorAt(0, QColor(255, 230, 120, 230))
    g.setColorAt(0.5, QColor(255, 120, 30, 160))
    g.setColorAt(1, QColor(255, 60, 0, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(g)
    p.drawEllipse(int(tx - r * 1.6), int(ty - r * 1.6), int(r * 3.2), int(r * 3.2))
    p.save()
    p.translate(cx, cy)
    p.rotate(giro)
    rg = QRadialGradient(-r * 0.3, -r * 0.3, r * 1.3)
    rg.setColorAt(0, QColor(170, 120, 80))
    rg.setColorAt(1, QColor(80, 50, 35))
    p.setPen(QPen(QColor(50, 30, 20), 1.5))
    p.setBrush(rg)
    p.drawEllipse(int(-r), int(-r), int(2 * r), int(2 * r))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(60, 40, 28, 170))
    for dx, dy, rr in ((-0.35, -0.2, 0.25), (0.3, 0.25, 0.2), (0.1, -0.45, 0.15)):
        p.drawEllipse(int(dx * r - rr * r), int(dy * r - rr * r), int(2 * rr * r), int(2 * rr * r))
    p.restore()


class ModoGame(QWidget):
    """🕹️ Jimmy no foguete com a pistola de laser contra ondas de meteoros; o Goddard ajuda de jetpack.
    Setas (ou WASD) pilotam, Espaço atira, Enter solta o redemoinho especial, P pausa, Esc sai."""
    PODERES = {"escudo": "🛡️", "triplo": "⚡", "vida": "❤️", "energia": "🌀"}
    INIMIGOS = {
        "blob":     {"voa": "alien_blob_voa", "dano": "alien_blob_dano", "fim": "alien_blob_fim", "hp": 1, "tam": 70, "vel": 3.2, "pts": 30, "onda": 2},
        "aranha":   {"voa": "alien_aranha_voa", "dano": "alien_aranha_dano", "fim": "alien_aranha_fim", "hp": 2, "tam": 80, "vel": 5.0, "pts": 40, "onda": 3},
        "cerebro":  {"voa": "alien_cerebro_voa", "dano": "alien_cerebro_dano", "fim": "alien_cerebro_fim", "ataca": "alien_cerebro_ataca",
                     "hp": 3, "tam": 85, "vel": 2.0, "pts": 60, "onda": 4, "atira": 85},
        "soldado":  {"voa": "yok_soldado", "voa2": "yok_aponta", "dano": "yok_dano", "fim": "yok_dano", "hp": 3, "tam": 95, "vel": 2.3, "pts": 60, "onda": 6},
        "atirador": {"voa": "yok_atirador", "dano": "yok_dano", "fim": "yok_dano", "hp": 3, "tam": 95, "vel": 2.0, "pts": 80, "onda": 7, "atira": 70},
    }

    def __init__(self, ao_sair):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        geo = tela_geo()
        self.setGeometry(geo)
        self.W, self.H = geo.width(), geo.height()
        self.ao_sair = ao_sair
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.k = max(0.75, vel())
        self.B = int(round(175 * self.k))      # Jimmy no foguete
        self.BG = int(round(105 * self.k))     # Goddard de jetpack
        self.cache = {}
        self.teclas = set()
        self.estrelas = [(random.uniform(0, self.W), random.uniform(0, self.H), random.uniform(0.6, 2.6)) for _ in range(110)]
        self.novo_jogo()
        self.timer = QTimer()
        self.timer.timeout.connect(self.passo)
        self.timer.start(30)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.grabKeyboard()

    # ---------- imagens ----------
    def img(self, anim, i, lado, espelho=False):
        caminho = Pet.frame(None, anim, i, None)
        if not caminho: return QPixmap()
        chave = (caminho, lado, espelho)
        if chave not in self.cache:
            pm = QPixmap(caminho)
            if not pm.isNull():
                pm = pm.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                if espelho: pm = pm.transformed(QTransform().scale(-1, 1))
            self.cache[chave] = pm
        return self.cache[chave]

    # ---------- partida ----------
    def novo_jogo(self):
        stat("game_partidas")
        self.jx, self.jy = self.W * 0.1, self.H * 0.4
        self.jvx = self.jvy = 0.0
        self.gx, self.gy = self.jx - self.BG, self.jy + self.B * 0.6
        self.vidas, self.pontos, self.combo, self.onda = 3, 0, 0, 0
        self.energia = 0.0
        self.lasers, self.lasers_gd, self.meteoros, self.particulas, self.poderes = [], [], [], [], []
        self.inimigos, self.tiros_ini, self.derrotados = [], [], []
        self.t = self.tiro_cd = self.tiro_t = self.inv = self.ferido = 0
        self.escudo = self.triplo = self.especial = self.flash = 0
        self.gd_cd, self.gd_tonto = 60, 0
        self.estado, self.estado_t = "contagem", 0
        self.msg, self.msg_t = "", 0
        self.intervalo = 0
        self.recorde_novo = False
        self.prox_onda()

    def prox_onda(self):
        self.onda += 1
        self.chefe = self.onda % 5 == 0
        self.a_lancar = (4 + self.onda) if self.chefe else (8 + 4 * self.onda)
        self.lancar_cd = 40
        if self.chefe and self.onda % 10 == 0 and Pet.frame(None, "yok_goobot", 0, None):
            self.lancar_goobot()
            self.aviso(f"Onda {self.onda}: REI GOOBOT! 👑", 100)
        elif self.chefe:
            self.lancar(chefe=True)
            self.aviso(f"Onda {self.onda}: METEORO CHEFE! ☄️", 90)
        else:
            self.aviso(f"Onda {self.onda}", 60)

    def aviso(self, texto, ticks=70):
        self.msg, self.msg_t = texto, ticks

    def lancar_inimigo(self, tipo, x=None, y=None):
        t = self.INIMIGOS[tipo]
        lado = int(t["tam"] * self.k)
        self.inimigos.append({"tipo": tipo, "x": self.W + lado / 2 if x is None else x,
                              "y": random.uniform(lado / 2 + 40, self.H - lado / 2 - 70) if y is None else y,
                              "y0": 0.0, "vx": -t["vel"] * self.k * random.uniform(0.85, 1.15) * (1 + 0.05 * (self.onda - 1)),
                              "hp": t["hp"], "lado": lado, "fase": random.uniform(0, 6.3), "dano": 0,
                              "atira": t.get("atira", 0) and random.randint(30, t["atira"]), "ataca": 0, "chefe": False})
        self.inimigos[-1]["y0"] = self.inimigos[-1]["y"]

    def lancar_goobot(self):
        lado = int(260 * self.k)
        self.inimigos.append({"tipo": "goobot", "x": self.W + lado / 2, "y": self.H / 2, "y0": self.H / 2, "vx": -1.5 * self.k,
                              "hp": 60 + 10 * self.onda, "hp0": 60 + 10 * self.onda, "lado": lado, "fase": 0.0, "dano": 0,
                              "atira": 90, "ataca": 0, "chefe": True, "chama": 200})

    def lancar(self, chefe=False):
        k = self.k
        # Da onda 2 em diante, parte das "pedras" vira alienígena
        if not chefe and random.random() < min(0.55, 0.12 * self.onda):
            tipos = [t for t, d in self.INIMIGOS.items() if d["onda"] <= self.onda and Pet.frame(None, d["voa"], 0, None)]
            if tipos:
                self.lancar_inimigo(random.choice(tipos))
                return
        if chefe:
            r, hp, vx = 70 * k, 25 + 5 * self.onda, -1.2 * k
        else:
            tam = random.choices((1, 2, 3), weights=(5, 3, min(4, self.onda)))[0]
            r, hp = (13, 21, 31)[tam - 1] * k, (1, 2, 4)[tam - 1]
            vx = -random.uniform(2.6, 4.6) * k * (1 + 0.1 * (self.onda - 1))
        self.meteoros.append({"x": self.W + r, "y": random.uniform(r + 50, self.H - r - 70), "vx": vx,
                              "vy": random.uniform(-0.7, 0.7) * k, "r": r, "hp": hp, "hp0": hp, "chefe": chefe,
                              "giro": random.uniform(0, 360), "fase": random.uniform(0, 6.3)})

    # ---------- teclado ----------
    def keyPressEvent(self, e):
        if e.isAutoRepeat(): return
        tecla = e.key()
        self.teclas.add(tecla)
        if tecla == Qt.Key.Key_Escape:
            self.sair()
        elif tecla == Qt.Key.Key_P and self.estado in ("jogando", "pausa"):
            self.estado = "pausa" if self.estado == "jogando" else "jogando"
        elif tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.estado == "fim": self.novo_jogo()
            elif self.estado == "jogando": self.usar_especial()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat(): self.teclas.discard(e.key())

    def focusOutEvent(self, e):
        # Trocou de janela (Alt+Tab): solta as teclas e pausa
        self.teclas.clear()
        if self.estado == "jogando": self.estado = "pausa"

    def mousePressEvent(self, e):
        self.activateWindow(); self.setFocus()

    def sair(self):
        self.timer.stop()
        self.releaseKeyboard()
        self.close()
        self.deleteLater()
        self.ao_sair(self.pontos, self.recorde_novo)

    # ---------- lógica ----------
    def passo(self):
        try:
            self.t += 1
            if self.estado == "contagem":
                self.estado_t += 1
                if self.estado_t >= 100: self.estado = "jogando"
            elif self.estado == "jogando":
                self.logica()
            if self.estado != "pausa":
                self.mexer_particulas()
                if self.msg_t > 0: self.msg_t -= 1
            self.update()
        except Exception as e:
            log_error(e)

    def segurando(self, *teclas):
        return any(t in self.teclas for t in teclas)

    def caixa_jimmy(self):
        return (self.jx + self.B * 0.2, self.jy + self.B * 0.2, self.jx + self.B * 0.85, self.jy + self.B * 0.85)

    def caixa_goddard(self):
        return (self.gx + self.BG * 0.15, self.gy + self.BG * 0.2, self.gx + self.BG * 0.85, self.gy + self.BG * 0.85)

    @staticmethod
    def bate(caixa, x, y, r):
        x0, y0, x1, y1 = caixa
        return math.hypot(x - max(x0, min(x, x1)), y - max(y0, min(y, y1))) < r

    def logica(self):
        k = self.k
        Q = Qt.Key
        dx = self.segurando(Q.Key_Right, Q.Key_D) - self.segurando(Q.Key_Left, Q.Key_A)
        dy = self.segurando(Q.Key_Down, Q.Key_S) - self.segurando(Q.Key_Up, Q.Key_W)
        lim = 10 * k
        self.jvx = max(-lim, min(lim, self.jvx * 0.86 + dx * 1.5 * k))
        self.jvy = max(-lim, min(lim, self.jvy * 0.86 + dy * 1.5 * k))
        self.jx = max(0, min(self.jx + self.jvx, self.W - self.B))
        self.jy = max(30, min(self.jy + self.jvy, self.H - self.B))
        if self.t % 2 == 0:
            self.fumaca(self.jx + self.B * 0.06, self.jy + self.B * 0.88)
        for nome in ("tiro_cd", "tiro_t", "inv", "ferido", "escudo", "triplo", "gd_tonto", "flash"):
            if getattr(self, nome) > 0: setattr(self, nome, getattr(self, nome) - 1)
        # Tiro (segurar Espaço = rajada)
        if self.segurando(Q.Key_Space) and not self.tiro_cd and not self.ferido and not self.especial:
            self.atirar()
        # Especial: carrega, solta o redemoinho e limpa a tela
        if self.especial:
            self.especial -= 1
            if self.especial == 55:
                self.flash = 12
                tocar("explosao")
                for m in list(self.meteoros):
                    if m["chefe"]:
                        m["hp"] -= 10
                        if m["hp"] <= 0: self.destruir(m)
                    else:
                        self.destruir(m)
                for a in list(self.inimigos):
                    a["hp"] -= 15 if a["chefe"] else 99
                    if a["hp"] <= 0: self.derrotar(a)
        self.mexer_lasers()
        self.mexer_goddard()
        self.mexer_meteoros()
        self.mexer_inimigos()
        self.mexer_poderes()
        # Ondas
        if self.a_lancar > 0:
            self.lancar_cd -= 1
            if self.lancar_cd <= 0:
                self.lancar()
                self.a_lancar -= 1
                self.lancar_cd = max(10, 38 - 3 * self.onda) * random.uniform(0.6, 1.4)
        elif not self.meteoros and not self.inimigos:
            self.intervalo += 1
            if self.intervalo == 1:
                bonus = 100 * self.onda
                self.pontos += bonus
                stat("game_ondas")
                self.aviso(f"Onda {self.onda} completa! +{bonus} 🎉", 80)
            if self.intervalo > 100:
                self.intervalo = 0
                self.prox_onda()

    def boca_arma(self):
        return self.jx + self.B * 0.86, self.jy + self.B * 0.43

    def atirar(self):
        x, y = self.boca_arma()
        self.lasers.append([x, y, 0.0])
        if self.triplo:
            self.lasers.append([x, y, -2.6 * self.k])
            self.lasers.append([x, y, 2.6 * self.k])
        self.tiro_cd, self.tiro_t = 7, 8
        tocar("laser")

    def usar_especial(self):
        if self.energia >= 1 and not self.especial:
            self.energia = 0.0
            self.especial = 75
            tocar("brainblast")
            self.aviso("⚡ BRAIN BLAST! 🌀", 60)

    def mexer_lasers(self):
        v = 24 * self.k
        for l in self.lasers + self.lasers_gd:
            l[0] += v if len(l) == 3 else l[3]
            l[1] += l[2]
        self.lasers = [l for l in self.lasers if l[0] < self.W + 40]
        self.lasers_gd = [l for l in self.lasers_gd if -40 < l[0] < self.W + 40 and -40 < l[1] < self.H + 40]
        for lista in (self.lasers, self.lasers_gd):
            for l in list(lista):
                for a in self.inimigos:
                    if a["x"] > -a["lado"] and math.hypot(l[0] - a["x"], l[1] - a["y"]) < a["lado"] * (0.32 if a["chefe"] else 0.4):
                        lista.remove(l)
                        a["hp"] -= 1
                        a["dano"] = 8
                        self.faiscas(l[0], l[1], 6, (190, 255, 120))
                        if a["hp"] <= 0: self.derrotar(a)
                        break
            for l in list(lista):
                for m in self.meteoros:
                    if math.hypot(l[0] - m["x"], l[1] - m["y"]) < m["r"] + 5:
                        lista.remove(l)
                        m["hp"] -= 1
                        self.faiscas(l[0], l[1], 5, (120, 230, 255) if lista is self.lasers else (255, 90, 90))
                        if m["hp"] <= 0: self.destruir(m)
                        break

    def mexer_goddard(self):
        k = self.k
        alvo = min(self.poderes, key=lambda pw: math.hypot(pw["x"] - self.gx, pw["y"] - self.gy), default=None)
        tx, ty = (alvo["x"] - self.BG / 2, alvo["y"] - self.BG / 2) if alvo else (self.jx - self.BG * 0.9, self.jy + self.B * 0.55)
        f = 0.06 if alvo else 0.08
        self.gx += (tx - self.gx) * f
        self.gy += (ty - self.gy) * f
        self.gx = max(0, min(self.gx, self.W - self.BG))
        self.gy = max(30, min(self.gy, self.H - self.BG))
        if self.t % 3 == 0:
            self.fumaca(self.gx + self.BG * 0.45, self.gy + self.BG * 0.9, pequena=True)
        # Ajudante: de tempos em tempos late um laser no meteoro mais perto à frente
        self.gd_cd -= 1
        if self.gd_cd <= 0 and not self.gd_tonto:
            bx, by = self.gx + self.BG * 0.85, self.gy + self.BG * 0.4
            frente = [m for m in self.meteoros + self.inimigos if m["x"] > bx and m["x"] < self.W]
            if frente:
                m = min(frente, key=lambda m: math.hypot(m["x"] - bx, m["y"] - by))
                d = max(1.0, math.hypot(m["x"] - bx, m["y"] - by))
                v = 18 * k
                self.lasers_gd.append([bx, by, (m["y"] - by) / d * v, (m["x"] - bx) / d * v])
                if random.random() < 0.35: tocar("latido")
            self.gd_cd = max(35, 75 - 4 * self.onda)

    def mexer_meteoros(self):
        caixa_j, caixa_g = self.caixa_jimmy(), self.caixa_goddard()
        for m in list(self.meteoros):
            m["x"] += m["vx"]
            m["y"] += m["vy"] + (math.sin(self.t * 0.03 + m["fase"]) * 1.2 * self.k if m["chefe"] else 0)
            m["giro"] += 2 if m["chefe"] else 5
            if m["y"] < m["r"] + 30 or m["y"] > self.H - m["r"]:
                m["vy"] = -m["vy"]
                m["y"] = max(m["r"] + 30, min(m["y"], self.H - m["r"]))
            if random.random() < 0.4:
                self.particulas.append({"x": m["x"] + m["r"], "y": m["y"] + random.uniform(-m["r"], m["r"]) * 0.5,
                                        "vx": 1.0, "vy": random.uniform(-0.3, 0.3), "r": m["r"] * 0.35, "vida": 22,
                                        "vida0": 22, "cor": (150, 140, 130), "tipo": "fumaca"})
            if m["x"] < -m["r"]:
                self.meteoros.remove(m)
                self.combo = 0                  # deixou passar
                if m["chefe"]: self.perder_vida()
                continue
            if self.bate(caixa_j, m["x"], m["y"], m["r"]) and not self.inv:
                if self.escudo:
                    self.escudo = 0
                    self.aviso("Escudo! 🛡️", 40)
                    self.destruir(m)
                else:
                    self.perder_vida()
                    if not m["chefe"]: self.explodir(m, pontos=False)
                continue
            if not self.gd_tonto and self.bate(caixa_g, m["x"], m["y"], m["r"]):
                self.gd_tonto = 60               # Goddard fica tonto, mas não perde vida
                tocar("goddard")
                if not m["chefe"]: self.explodir(m, pontos=False)

    def mexer_inimigos(self):
        k = self.k
        caixa_j, caixa_g = self.caixa_jimmy(), self.caixa_goddard()
        cx_j, cy_j = self.jx + self.B * 0.5, self.jy + self.B * 0.5
        for a in list(self.inimigos):
            a["fase"] += 0.05
            if a["dano"]: a["dano"] -= 1
            if a["ataca"]: a["ataca"] -= 1
            tipo = a["tipo"]
            if a["chefe"]:
                # Rei Goobot: entra, para à direita, sobe e desce, atira em leque e chama blobs
                if a["x"] > self.W * 0.78: a["x"] += a["vx"]
                amp = max(0.0, min(self.H * 0.3, self.H / 2 - a["lado"] / 2 - 50))   # barra de vida sempre visível
                a["y"] = self.H / 2 + math.sin(a["fase"] * 0.6) * amp
                a["atira"] -= 1
                if a["atira"] <= 0:
                    for ang in (-0.35, -0.12, 0.12, 0.35):
                        self.tiros_ini.append([a["x"] - a["lado"] * 0.3, a["y"], -7 * k * math.cos(ang), 7 * k * math.sin(ang), (120, 255, 90)])
                    a["atira"], a["ataca"] = max(45, 90 - 3 * self.onda), 15
                    tocar("laser")
                a["chama"] -= 1
                if a["chama"] <= 0:
                    for dy in (-90, 90):
                        self.lancar_inimigo("blob", x=a["x"] - a["lado"] * 0.3, y=max(80, min(a["y"] + dy * k, self.H - 120)))
                    a["chama"] = 220
            else:
                a["x"] += a["vx"]
                if tipo == "blob":
                    a["y"] = a["y0"] + math.sin(a["fase"] * 2) * 60 * k
                elif tipo == "aranha":
                    a["y"] += max(-2.5 * k, min(2.5 * k, (cy_j - a["y"]) * 0.02))   # mergulha na sua direção
                else:
                    a["y"] = a["y0"] + math.sin(a["fase"]) * 35 * k
                if a["atira"]:
                    a["atira"] -= 1
                    if a["atira"] <= 0 and a["x"] < self.W - 40:
                        d = max(1.0, math.hypot(cx_j - a["x"], cy_j - a["y"]))
                        cor = (200, 120, 255) if tipo == "cerebro" else (255, 80, 60)
                        self.tiros_ini.append([a["x"] - a["lado"] * 0.35, a["y"], (cx_j - a["x"]) / d * 7.5 * k, (cy_j - a["y"]) / d * 7.5 * k, cor])
                        a["atira"], a["ataca"] = self.INIMIGOS[tipo]["atira"], 12
                        tocar("laser")
            if a["x"] < -a["lado"]:
                self.inimigos.remove(a)
                self.combo = 0
                continue
            raio = a["lado"] * (0.3 if a["chefe"] else 0.38)
            if not self.inv and self.bate(caixa_j, a["x"], a["y"], raio):
                if self.escudo:
                    self.escudo = 0
                    self.aviso("Escudo! 🛡️", 40)
                    if not a["chefe"]: self.derrotar(a)
                else:
                    self.perder_vida()
                    if not a["chefe"]: self.derrotar(a, pontos=False)
                continue
            if not a["chefe"] and not self.gd_tonto and self.bate(caixa_g, a["x"], a["y"], raio):
                self.gd_tonto = 60
                tocar("goddard")
        # Tiros dos inimigos
        for t in list(self.tiros_ini):
            t[0] += t[2]; t[1] += t[3]
            if not (-30 < t[0] < self.W + 30 and -30 < t[1] < self.H + 30):
                self.tiros_ini.remove(t)
            elif self.bate(caixa_j, t[0], t[1], 6 * k) and not self.inv:
                self.tiros_ini.remove(t)
                if self.escudo:
                    self.escudo = 0
                    self.aviso("Escudo! 🛡️", 40)
                else:
                    self.perder_vida()
            elif not self.gd_tonto and self.bate(caixa_g, t[0], t[1], 6 * k):
                self.tiros_ini.remove(t)
                self.gd_tonto = 60
                tocar("goddard")
        # Derrotados caindo
        for d in self.derrotados:
            d["y"] += d["vy"]; d["vy"] += 0.4 * k; d["x"] += d["vx"]; d["vida"] -= 1
        self.derrotados = [d for d in self.derrotados if d["vida"] > 0 and d["y"] < self.H + 100]

    def derrotar(self, a, pontos=True):
        if a in self.inimigos: self.inimigos.remove(a)
        self.faiscas(a["x"], a["y"], 16, (190, 255, 120))
        tocar("estouro")
        anim = "yok_goobot" if a["chefe"] else self.INIMIGOS[a["tipo"]]["fim"]
        self.derrotados.append({"anim": anim, "x": a["x"], "y": a["y"], "vx": -1.0 * self.k, "vy": -4 * self.k,
                                "lado": a["lado"], "vida": 60, "giro": 0})
        if not pontos: return
        self.combo += 1
        mult = min(5, 1 + self.combo // 5)
        base = 1500 if a["chefe"] else self.INIMIGOS[a["tipo"]]["pts"]
        self.pontos += base * mult
        self.energia = min(1.0, self.energia + (0.8 if a["chefe"] else 0.08))
        if a["chefe"]:
            self.aviso("Rei Goobot derrotado! +1500 👑", 100)
            tocar("fogos")
            self.poderes.append({"x": a["x"], "y": a["y"], "tipo": "vida", "fase": 0.0})
            # Os blobs que ele chamou fogem
            for b in list(self.inimigos): self.derrotar(b, pontos=False)
        elif random.random() < 0.15:
            self.poderes.append({"x": a["x"], "y": a["y"], "tipo": random.choice(list(self.PODERES)), "fase": random.uniform(0, 6)})

    def perder_vida(self):
        self.vidas -= 1
        self.combo = 0
        self.ferido, self.inv = 35, 100
        tocar("pouso")
        self.faiscas(self.jx + self.B / 2, self.jy + self.B / 2, 18, (255, 200, 80))
        if self.vidas <= 0:
            self.estado = "fim"
            tocar("explosao")
            if self.pontos > CFG["game_recorde"]:
                CFG["game_recorde"] = self.pontos
                self.recorde_novo = True
                save_cfg(CFG)

    def explodir(self, m, pontos=True):
        if m in self.meteoros: self.meteoros.remove(m)
        self.faiscas(m["x"], m["y"], int(10 + m["r"] / 2), (255, 170, 60))
        for _ in range(int(3 + m["r"] / 8)):
            self.particulas.append({"x": m["x"] + random.uniform(-m["r"], m["r"]) * 0.5, "y": m["y"] + random.uniform(-m["r"], m["r"]) * 0.5,
                                    "vx": random.uniform(-1, 1), "vy": random.uniform(-1, 1), "r": m["r"] * 0.5, "vida": 35,
                                    "vida0": 35, "cor": (120, 110, 100), "tipo": "fumaca"})
        tocar("estouro")

    def destruir(self, m):
        self.explodir(m)
        self.combo += 1
        mult = min(5, 1 + self.combo // 5)
        base = 500 if m["chefe"] else {1: 10, 2: 25}.get(m["hp0"], 50)
        self.pontos += base * mult
        self.energia = min(1.0, self.energia + (0.6 if m["chefe"] else 0.06))
        if m["chefe"]:
            self.aviso("Chefe derrotado! +500 🏆", 80)
            self.poderes.append({"x": m["x"], "y": m["y"], "tipo": "vida", "fase": 0.0})
        elif m["hp0"] == 4:
            # O grande racha em dois pequenos
            for vy in (-1.6, 1.6):
                self.meteoros.append({"x": m["x"], "y": m["y"], "vx": m["vx"] * 1.2, "vy": vy * self.k, "r": 13 * self.k,
                                      "hp": 1, "hp0": 1, "chefe": False, "giro": 0.0, "fase": 0.0})
        if not m["chefe"] and random.random() < 0.1:
            self.poderes.append({"x": m["x"], "y": m["y"], "tipo": random.choice(list(self.PODERES)), "fase": random.uniform(0, 6)})

    def mexer_poderes(self):
        caixa_j, caixa_g = self.caixa_jimmy(), self.caixa_goddard()
        for pw in list(self.poderes):
            pw["x"] -= 1.5 * self.k
            pw["fase"] += 0.1
            pw["y"] += math.sin(pw["fase"]) * 0.8
            if self.bate(caixa_j, pw["x"], pw["y"], 16 * self.k) or self.bate(caixa_g, pw["x"], pw["y"], 16 * self.k):
                self.poderes.remove(pw)
                tocar("bolinha")
                tipo = pw["tipo"]
                if tipo == "escudo": self.escudo = 330
                elif tipo == "triplo": self.triplo = 300
                elif tipo == "vida": self.vidas = min(5, self.vidas + 1)
                else: self.energia = min(1.0, self.energia + 0.5)
                self.aviso({"escudo": "🛡️ Escudo!", "triplo": "⚡ Tiro triplo!", "vida": "❤️ +1 vida!",
                            "energia": "🌀 Energia!"}[tipo], 45)
            elif pw["x"] < -30:
                self.poderes.remove(pw)

    # ---------- partículas ----------
    def fumaca(self, x, y, pequena=False):
        r = (4 if pequena else 7) * self.k
        self.particulas.append({"x": x, "y": y + random.uniform(-4, 4), "vx": -random.uniform(2, 4) * self.k,
                                "vy": random.uniform(-0.4, 0.4), "r": r, "vida": 26, "vida0": 26,
                                "cor": (235, 235, 240), "tipo": "fumaca"})

    def faiscas(self, x, y, n, cor):
        for _ in range(n):
            a = random.uniform(0, 6.3)
            v = random.uniform(2, 7) * self.k
            self.particulas.append({"x": x, "y": y, "vx": math.cos(a) * v, "vy": math.sin(a) * v, "r": 2.5 * self.k,
                                    "vida": random.randint(12, 26), "vida0": 26, "cor": cor, "tipo": "faisca"})

    def mexer_particulas(self):
        for q in self.particulas:
            q["x"] += q["vx"]; q["y"] += q["vy"]
            q["vida"] -= 1
            if q["tipo"] == "fumaca": q["r"] *= 1.03
            else: q["vx"] *= 0.93; q["vy"] *= 0.93
        self.particulas = [q for q in self.particulas if q["vida"] > 0][-500:]

    # ---------- desenho ----------
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        k = self.k
        # Céu escurecido com estrelas passando (sensação de voo)
        p.fillRect(self.rect(), QColor(6, 10, 32, 165))
        p.setPen(Qt.PenStyle.NoPen)
        for x, y, sz in self.estrelas:
            xx = (x - self.t * sz * 1.2) % self.W
            p.setBrush(QColor(255, 255, 255, int(90 + sz * 60)))
            p.drawEllipse(int(xx), int(y), int(sz + 0.5), int(sz + 0.5))
        for q in self.particulas:
            a = max(0.0, q["vida"] / q["vida0"])
            r, g, b = q["cor"]
            p.setBrush(QColor(r, g, b, int((110 if q["tipo"] == "fumaca" else 255) * a)))
            p.drawEllipse(int(q["x"] - q["r"]), int(q["y"] - q["r"]), int(2 * q["r"]), int(2 * q["r"]))
        # Power-ups
        f = p.font()
        for pw in self.poderes:
            rr = 17 * k
            p.setBrush(QColor(255, 255, 255, 200))
            p.setPen(QPen(QColor(120, 200, 255), 2))
            p.drawEllipse(int(pw["x"] - rr), int(pw["y"] - rr), int(2 * rr), int(2 * rr))
            f.setPointSize(int(13 * k)); p.setFont(f)
            p.drawText(int(pw["x"] - rr), int(pw["y"] - rr), int(2 * rr), int(2 * rr), Qt.AlignmentFlag.AlignCenter, self.PODERES[pw["tipo"]])
        p.setPen(Qt.PenStyle.NoPen)
        # Meteoros (o chefe tem barra de vida)
        for m in self.meteoros:
            desenhar_meteoro(p, m["x"], m["y"], m["r"], m["giro"], m["vx"], m["vy"])
            if m["chefe"]:
                w = m["r"] * 2
                p.setBrush(QColor(60, 0, 0, 200))
                p.drawRect(int(m["x"] - w / 2), int(m["y"] - m["r"] - 18), int(w), 8)
                p.setBrush(QColor(255, 60, 60))
                p.drawRect(int(m["x"] - w / 2), int(m["y"] - m["r"] - 18), int(w * max(0, m["hp"]) / m["hp0"]), 8)
        # Alienígenas (espelhados: olham para o Jimmy)
        for a in self.inimigos:
            if a["chefe"]:
                anim, i = "yok_goobot", 0
            else:
                t = self.INIMIGOS[a["tipo"]]
                if a["dano"]: anim, i = t["dano"], 0
                elif a["ataca"] and "ataca" in t: anim, i = t["ataca"], 0
                elif "voa2" in t: anim, i = (t["voa"], 0) if (self.t // 20) % 2 else (t["voa2"], 0)
                else: anim, i = t["voa"], self.t // 8
            pm = self.img(anim, i, a["lado"], espelho=True)
            if a["chefe"] and a["dano"]:
                p.setOpacity(0.6)
            p.drawPixmap(int(a["x"] - pm.width() / 2), int(a["y"] - pm.height() / 2), pm)
            p.setOpacity(1.0)
            if a["chefe"]:
                w = a["lado"] * 0.8
                p.setBrush(QColor(40, 0, 40, 200))
                p.drawRect(int(a["x"] - w / 2), int(a["y"] - a["lado"] / 2 - 16), int(w), 9)
                p.setBrush(QColor(140, 255, 90))
                p.drawRect(int(a["x"] - w / 2), int(a["y"] - a["lado"] / 2 - 16), int(w * max(0, a["hp"]) / a["hp0"]), 9)
        for d in self.derrotados:
            pm = self.img(d["anim"], 0, d["lado"], espelho=True)
            p.setOpacity(max(0.0, d["vida"] / 60))
            p.drawPixmap(int(d["x"] - pm.width() / 2), int(d["y"] - pm.height() / 2), pm)
            p.setOpacity(1.0)
        for t in self.tiros_ini:
            r, g, b = t[4]
            p.setBrush(QColor(r, g, b, 90))
            p.drawEllipse(int(t[0] - 9 * self.k), int(t[1] - 9 * self.k), int(18 * self.k), int(18 * self.k))
            p.setBrush(QColor(255, 255, 255))
            p.drawEllipse(int(t[0] - 4 * self.k), int(t[1] - 4 * self.k), int(8 * self.k), int(8 * self.k))
        # Lasers
        for l in self.lasers:
            for larg, cor in ((7, QColor(80, 200, 255, 90)), (3, QColor(220, 250, 255))):
                p.setPen(QPen(cor, larg * k, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(int(l[0] - 34 * k), int(l[1] - l[2] * 1.4), int(l[0]), int(l[1]))
        for l in self.lasers_gd:
            d = max(1.0, math.hypot(l[2], l[3]))
            for larg, cor in ((6, QColor(255, 80, 80, 90)), (2.5, QColor(255, 220, 220))):
                p.setPen(QPen(cor, larg * k, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(int(l[0] - l[3] / d * 22 * k), int(l[1] - l[2] / d * 22 * k), int(l[0]), int(l[1]))
        p.setPen(Qt.PenStyle.NoPen)
        # Goddard de jetpack
        anim = "goddard_hover_scared" if self.gd_tonto else "goddard_fly"
        p.drawPixmap(int(self.gx), int(self.gy), self.img(anim, self.t // 4, self.BG))
        # Jimmy no foguete
        if self.especial:
            anim, i = ("game_carrega", 0) if self.especial > 55 else ("game_especial", 0)
        elif self.ferido:
            anim, i = "game_atingido", 0
        elif self.tiro_t:
            anim, i = "game_tiro", 0 if self.tiro_t > 4 else 1
        elif abs(self.jvy) > 7 * k:
            anim, i = "game_desvia", 0
        else:
            anim, i = "game_voa", self.t // 6
        if not (self.inv and not self.ferido and (self.t // 3) % 2):
            p.drawPixmap(int(self.jx), int(self.jy), self.img(anim, i, self.B))
        if self.escudo and (self.escudo > 60 or (self.t // 4) % 2):
            p.setPen(QPen(QColor(120, 210, 255, 200), 3))
            p.setBrush(QColor(120, 210, 255, 45))
            p.drawEllipse(int(self.jx + self.B * 0.05), int(self.jy + self.B * 0.05), int(self.B * 0.9), int(self.B * 0.9))
            p.setPen(Qt.PenStyle.NoPen)
        if self.flash:
            p.fillRect(self.rect(), QColor(200, 240, 255, int(self.flash * 15)))
        self.desenhar_hud(p)

    def texto(self, p, x, y, w, h, txt, tam, cor=QColor(255, 255, 255), alinhar=Qt.AlignmentFlag.AlignLeft):
        f = p.font(); f.setPointSize(int(tam)); f.setBold(True); p.setFont(f)
        p.setPen(QColor(0, 0, 0, 180))
        p.drawText(int(x + 2), int(y + 2), int(w), int(h), alinhar | Qt.AlignmentFlag.AlignVCenter, txt)
        p.setPen(cor)
        p.drawText(int(x), int(y), int(w), int(h), alinhar | Qt.AlignmentFlag.AlignVCenter, txt)

    def desenhar_hud(self, p):
        W, H = self.W, self.H
        C = Qt.AlignmentFlag.AlignHCenter
        self.texto(p, 20, 10, 400, 30, "❤️" * max(0, self.vidas), 16)
        self.texto(p, 20, 42, 500, 30, tr(f"Pontos: {self.pontos}"), 16)
        mult = min(5, 1 + self.combo // 5)
        info = tr(f"Onda {self.onda}") + (f"   x{mult} 🔥" if mult > 1 else "")
        self.texto(p, 20, 74, 500, 30, info, 13, QColor(255, 220, 120))
        # Barra do especial
        bx, by, bw = 22, 112, 180
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 60)); p.drawRoundedRect(bx, by, bw, 12, 6, 6)
        cheia = self.energia >= 1
        p.setBrush(QColor(120, 220, 255) if not cheia or (self.t // 6) % 2 else QColor(255, 255, 255))
        p.drawRoundedRect(bx, by, int(bw * self.energia), 12, 6, 6)
        self.texto(p, bx + bw + 8, by - 8, 260, 28, tr("🌀 ENTER!") if cheia else "🌀", 11, QColor(160, 230, 255))
        self.texto(p, W - 420, 10, 400, 30, tr(f"🏆 Recorde: {max(CFG['game_recorde'], self.pontos)}"), 14,
                   QColor(255, 220, 120), Qt.AlignmentFlag.AlignRight)
        self.texto(p, 0, H - 40, W, 30, tr("Setas: pilotar · Espaço: atirar · Enter: especial · P: pausa · Esc: sair"), 10,
                   QColor(255, 255, 255, 190), C)
        if self.msg_t:
            a = min(255, self.msg_t * 12)
            self.texto(p, 0, H * 0.18, W, 50, tr(self.msg), 24, QColor(255, 255, 255, a), C)
        if self.estado == "contagem":
            n = 3 - self.estado_t // 25
            self.texto(p, 0, H * 0.35, W, 120, str(n) if n > 0 else tr("VAI! 🚀"), 64, QColor(255, 230, 120), C)
        elif self.estado == "pausa":
            self.texto(p, 0, H * 0.38, W, 80, tr("⏸️ Pausa (P para voltar)"), 32, QColor(255, 255, 255), C)
        elif self.estado == "fim":
            p.setBrush(QColor(0, 0, 0, 170)); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(int(W / 2 - 300), int(H * 0.28), 600, 230, 20, 20)
            self.texto(p, 0, H * 0.28 + 15, W, 60, tr("Fim de jogo!"), 34, QColor(255, 120, 100), C)
            self.texto(p, 0, H * 0.28 + 80, W, 50, tr(f"{self.pontos} pontos · onda {self.onda}"), 22, QColor(255, 255, 255), C)
            if self.recorde_novo:
                self.texto(p, 0, H * 0.28 + 128, W, 40, tr("🏆 Novo recorde!"), 20, QColor(255, 220, 120), C)
            self.texto(p, 0, H * 0.28 + 175, W, 40, tr("Enter: jogar de novo · Esc: sair"), 14, QColor(220, 220, 220), C)


class Planeta(QWidget):
    """Planeta no alto da tela com uma lhama perdida em cima (o Jimmy vai buscar)."""
    def __init__(self, cx):
        super().__init__()
        _overlay_flags(self)
        k = vel()
        self.lado = int(230 * k)
        self.setFixedSize(self.lado, self.lado)
        caminho = Pet.frame(None, "planeta", 0, None)
        pm = QPixmap(caminho) if caminho else QPixmap()
        self.pm = pm.scaled(self.lado, self.lado, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation) if not pm.isNull() else pm
        lh = Pet.frame(None, random.choice(["lhama_marrom", "lhama_branca"]), 0, None)
        self.lhama_anim = os.path.basename(os.path.dirname(lh)) if lh else "lhama_marrom"
        lpm = QPixmap(lh) if lh else QPixmap()
        self.lhama = lpm.scaled(int(80 * k), int(80 * k), Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation) if not lpm.isNull() else lpm
        self.com_lhama = True
        # No quadro extraído o planeta ocupa a parte de baixo: o topo da esfera fica a ~40% da altura
        self.cx = max(self.lado / 2, min(cx, tela_geo().width() - self.lado / 2))
        self.topo = 10
        self.chao_lhama = self.topo + self.lado * 0.42     # onde a lhama pisa (sem OX/OY)
        self.alpha, self.alvo_alpha, self.t = 0.0, 1.0, 0
        self.move(int(self.cx - self.lado / 2) + OX, int(self.topo) + OY)
        self.timer = QTimer()
        self.timer.timeout.connect(self.passo)
        self.timer.start(30)
        self.show()

    def passo(self):
        self.t += 1
        self.alpha += (self.alvo_alpha - self.alpha) * 0.05
        if self.alvo_alpha == 0 and self.alpha < 0.02:
            self.timer.stop()
            self.close()
            self.deleteLater()
            return
        self.update()

    def sumir(self):
        self.alvo_alpha = 0.0

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setOpacity(self.alpha)
        bob = math.sin(self.t * 0.04) * 3
        p.drawPixmap(int((self.lado - self.pm.width()) / 2), int(bob), self.pm)
        if self.com_lhama and not self.lhama.isNull():
            # Em pé no alto do planeta, olhando de um lado para o outro
            lh = self.lhama if (self.t // 60) % 2 else self.lhama.transformed(QTransform().scale(-1, 1))
            p.drawPixmap(int(self.lado / 2 - lh.width() / 2), int(bob + self.lado * 0.42 - lh.height()), lh)


class LhamaCarona(QWidget):
    """A lhama resgatada voltando de carona no foguete do Jimmy."""
    def __init__(self, anim):
        super().__init__()
        _overlay_flags(self)
        k = vel()
        lh = Pet.frame(None, anim, 0, None)
        pm = QPixmap(lh) if lh else QPixmap()
        self.pm = pm.scaled(int(70 * k), int(70 * k), Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation) if not pm.isNull() else pm
        self.setFixedSize(max(1, self.pm.width()), max(1, self.pm.height()))
        self.virada = False
        self.show()

    def follow(self, j, flip):
        self.virada = flip
        self.move(int(j.x + j.box * (0.62 if flip else 0.18)) + OX, int(j.y + j.box * 0.22) + OY)
        _topmost(self)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0, 0, self.pm.transformed(QTransform().scale(-1, 1)) if self.virada else self.pm)


class MedidorGoddard(QWidget):
    """Painelzinho em cima do Goddard: óleo, diversão e limpeza."""
    def __init__(self):
        super().__init__()
        _overlay_flags(self)
        self.setFixedSize(96, 46)

    def follow(self, pet):
        top = getattr(pet, "content_top", 0)
        self.move(int(pet.x + pet.box / 2 - 48) + OX, int(pet.y + top - 50) + OY)
        if not self.isVisible(): self.show()
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(40, 40, 40, 200))
        p.setBrush(QColor(255, 255, 255, 225))
        p.drawRoundedRect(0, 0, 95, 45, 8, 8)
        f = p.font(); f.setPointSize(8); p.setFont(f)
        for i, (k, ico) in enumerate(GD_ITENS):
            y = 4 + i * 13
            p.setPen(QColor(0, 0, 0))
            p.drawText(5, y + 10, ico)
            v = gd_get(k)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(220, 220, 220))
            p.drawRoundedRect(24, y + 2, 64, 8, 3, 3)
            cor = QColor(70, 190, 90) if v >= 60 else QColor(240, 190, 40) if v >= 30 else QColor(225, 70, 60)
            p.setBrush(cor)
            p.drawRoundedRect(24, y + 2, int(64 * v / 100), 8, 3, 3)

class Meteoro(QWidget):
    """Meteoro em chamas: clique para explodir antes que chegue no chão."""
    def __init__(self, x, alvo_x, chao, on_fim):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.CrossCursor)
        k = vel()
        self.r = max(10, int(17 * k))
        self.lado = self.r * 4
        self.setFixedSize(self.lado, self.lado)
        self.fx, self.fy = x, -self.lado
        self.chao = chao
        dist = math.hypot(alvo_x - x, chao - self.fy)
        vel_m = random.uniform(2.6, 4.2) * k
        self.vx, self.vy = (alvo_x - x) / dist * vel_m, (chao - self.fy) / dist * vel_m
        self.on_fim = on_fim
        self.giro = random.uniform(0, 360)
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)
        self.timer.start(30)
        self.place()
        self.show()

    def place(self):
        self.move(int(self.fx - self.lado / 2) + OX, int(self.fy - self.lado / 2) + OY)

    def step(self):
        self.fx += self.vx
        self.fy += self.vy
        self.giro += 6
        if FX and random.random() < 0.5:
            FX.smoke(self.fx - self.vx * 4, self.fy - self.vy * 4, random.uniform(3, 5), life=25,
                     gray=random.randint(120, 170), alpha=0.4, grow=1.5)
        if self.fy >= self.chao - self.r:
            self.acabar(acertou=False)
            return
        self.place()
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.lado / 2
        desenhar_meteoro(p, c, c, self.r, self.giro, self.vx, self.vy)

    def mousePressEvent(self, e):
        self.acabar(acertou=True)

    def acabar(self, acertou):
        if not self.timer.isActive(): return
        self.timer.stop()
        if FX:
            if acertou:
                FX.sparks(self.fx, self.fy, 28, colors=[(255, 220, 120), (255, 140, 40), (200, 160, 120)], speed=(2, 7))
            else:
                FX.sparks(self.fx, self.fy, 14, colors=[(255, 160, 60), (150, 110, 80)], speed=(1, 4))
                for _ in range(5):
                    FX.smoke(self.fx + random.uniform(-10, 10), self.fy, random.uniform(6, 10), life=45,
                             gray=random.randint(110, 150), alpha=0.5, grow=2.0)
        tocar("pouso")
        self.on_fim(self, acertou)
        self.close()
        self.deleteLater()

class Bubble(QWidget):
    """Balão de fala dos lembretes. Clicar fecha."""
    def __init__(self, on_click):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.on_click = on_click
        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #222; font: bold 12px 'Segoe UI';")
        self.tail = 10

    def say(self, text):
        self.label.setText(tr(text))
        self.label.setFixedWidth(170)
        self.label.adjustSize()
        w, h = 190, self.label.height() + 20
        self.label.move(10, 10)
        self.setFixedSize(w, h + self.tail)

    def follow(self, pet):
        # Em cima da cabeça do Jimmy, com a ponta apontando para ele
        top = getattr(pet, "content_top", pet.box * 0.08)
        self.move(int(pet.x + pet.box / 2 - self.width() / 2) + OX, int(pet.y + top - self.height() + 4) + OY)
        if not self.isVisible(): self.show()
        self.raise_()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height() - self.tail
        p.setPen(QColor(40, 40, 40))
        p.setBrush(QColor(255, 255, 255, 245))
        p.drawRoundedRect(1, 1, w - 2, h - 2, 12, 12)
        # Ponta do balão
        from PyQt6.QtGui import QPolygon
        p.drawPolygon(QPolygon([QPoint(w // 2 - 9, h - 2), QPoint(w // 2 + 9, h - 2), QPoint(w // 2, h + self.tail - 1)]))
        p.setPen(QColor(255, 255, 255, 245))
        p.drawLine(w // 2 - 8, h - 2, w // 2 + 8, h - 2)

    def mousePressEvent(self, e):
        self.on_click()

class Pet(QWidget):
    shadow_ratio = None  # largura da sombra em relação à janela (None = sem sombra)
    shadow = None
    def __init__(self, name, image_folder, default_img, x, y):
        super().__init__()
        self.name = name
        self.image_folder = image_folder
        self.box = 150  # lado da janela do pet em pixels
        self.depth = 1.0  # perspectiva: 1 no chão, até 0,7 no alto da tela
        screen_geo = tela_geo()
        self.sw, self.sh = screen_geo.width(), screen_geo.height()

        # Janela sem bordas, sempre no topo e Tool para não aparecer na barra de tarefas do Windows
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Label para a imagem
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Garante que o label seja visível
        self.label.show()

        self.set_image(default_img)

        # Tamanho fixo da janela do pet
        self.setFixedSize(QSize(self.box, self.box))
        self.label.setFixedSize(QSize(self.box, self.box))

        self.x = x
        self.y = y
        self.move(int(self.x), int(self.y))

        self.direction = 1
        self.speed = 2
        self.state = "walking"

    def set_image(self, img_name, flip=False, angle=0):
        self._last_img = (img_name, flip, angle)
        if not img_name: return
        if not img_name.lower().endswith(".png"):
            img_name += ".png"
        # Só redesenha quando a imagem (ou a inclinação) muda
        angle = round(angle)
        tint = noite_tint()
        if (img_name, flip, angle, self.box, tint) == getattr(self, "current_img", None): return
        self.current_img = (img_name, flip, angle, self.box, tint)

        # Cache das imagens já carregadas para não ler do disco toda hora
        if not hasattr(self, "pix_cache"): self.pix_cache = {}
        path = img_name if os.path.isabs(img_name) else os.path.join(self.image_folder, img_name)
        key = (img_name, self.box)
        if key not in self.pix_cache:
            print(f"TENTANDO CARREGAR: {path}") # Log para depuração no terminal
            if not os.path.exists(path):
                print(f"ERRO: Arquivo não encontrado: {path}")
                self.label.setText("❓")
                return
            pixmap = QPixmap(path)
            if pixmap.isNull():
                print(f"ERRO: Imagem {path} está corrompida ou é inválida.")
                self.label.setText("🖼️")
                return
            self.pix_cache[key] = pixmap.scaled(self.box, self.box, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Primeira linha com desenho (para o balão de fala encostar na cabeça)
            qi = self.pix_cache[key].toImage()
            top = 0
            for yy in range(0, qi.height(), 2):
                if any(qi.pixelColor(xx, yy).alpha() > 40 for xx in range(0, qi.width(), 3)):
                    top = yy
                    break
            if not hasattr(self, "top_cache"): self.top_cache = {}
            self.top_cache[key] = top + (self.box - qi.height()) // 2

        pixmap = self.pix_cache.get(key)
        self.content_top = getattr(self, "top_cache", {}).get(key, 0)
        if pixmap is not None:
            if flip or angle:
                transform = QTransform()
                if angle: transform.rotate(angle)
                if flip: transform.scale(-1, 1)
                pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            if tint > 0:
                # À noite: tom azulado escuro só por cima do desenho (o fundo continua transparente)
                pixmap = QPixmap(pixmap)
                pt = QPainter(pixmap)
                pt.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
                pt.fillRect(pixmap.rect(), QColor(15, 25, 70, int(90 * tint)))
                pt.end()

            self.label.setPixmap(pixmap)
            self.label.setScaledContents(False)

    anim_cache = {}

    def frame(self, anim, i, fallback):
        """Caminho do quadro i (em loop) da animação; usa a imagem antiga se a pasta não existir."""
        if anim not in Pet.anim_cache:
            folder = os.path.join(ANIM_DIR, anim)
            files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".png")) if os.path.isdir(folder) else []
            Pet.anim_cache[anim] = [os.path.join(folder, f) for f in files]
            if not files:
                log_error(FileNotFoundError(f"animação '{anim}' não encontrada em {ANIM_DIR}"))
        frames = Pet.anim_cache[anim]
        return frames[i % len(frames)] if frames else fallback

    def set_box(self, size, anchor="bottom"):
        """Muda o tamanho da janela mantendo o pet no lugar (pés no chão ou centro)."""
        if size == self.box: return
        d = size - self.box
        self.x -= d / 2
        self.y -= d if anchor == "bottom" else d / 2
        self.box = size
        self.setFixedSize(QSize(size, size))
        self.label.setFixedSize(QSize(size, size))
        self.current_img = None
        self.move(int(self.x), int(self.y))

    box_cache = {}

    def anim_box(self, anim):
        """Tamanho da janela para a animação (meta.json gerado pelo extract_frames.py) x ESCALA."""
        if anim not in Pet.box_cache:
            box = 150
            try:
                with open(os.path.join(ANIM_DIR, anim, "meta.json"), encoding="utf-8") as f:
                    box = json.load(f).get("box", 150)
            except (OSError, ValueError):
                pass
            # O Goddard ainda tem a proporção dele (em relação ao Jimmy)
            prop = CFG["tamanho_goddard"] / 100 if anim.startswith("goddard_") else 1.0
            Pet.box_cache[anim] = int(round(box * ESCALA * prop))
        return Pet.box_cache[anim]

    def show_anim(self, anim, i, flip=False, angle=0, anchor="bottom", fallback=None):
        """Mostra o quadro i da animação já no tamanho certo dela."""
        self.set_box(int(round(self.anim_box(anim) * self.depth)), anchor)
        self.set_image(self.frame(anim, i, fallback), flip=flip, angle=angle)

    @property
    def ground_y(self):
        # Pés em cima da barra de tarefas, qualquer que seja o tamanho da janela
        chao = chao_em(self.x + self.box / 2)
        return (chao if chao is not None else self.sh) - 10 - self.box

    def update_depth(self):
        """Quanto mais alto, menor (até 30%); volta ao normal perto do chão. Em degraus de 5%."""
        feet = self.y + self.box
        alt = max(0.0, (self.sh - 10) - feet)
        frac = min(1.0, alt / (self.sh * 0.75))
        self.depth = round((1 - 0.3 * frac) * 20) / 20

    def has_anim(self, anim):
        # Só pergunta se existe (não registra erro: várias animações são opcionais)
        if anim not in Pet.anim_cache:
            folder = os.path.join(ANIM_DIR, anim)
            if not (os.path.isdir(folder) and any(f.lower().endswith(".png") for f in os.listdir(folder))):
                return False
        return bool(self.frame(anim, 0, None))

    def keep_on_top(self):
        # A barra de tarefas também é "sempre no topo"; ao clicar nela o Windows a coloca na frente.
        # Reafirma o pet por cima (HWND_TOPMOST) sem roubar o foco.
        if not self.isVisible(): return
        try:
            ctypes.windll.user32.SetWindowPos(int(self.winId()), -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except (AttributeError, OSError):
            self.raise_()

    def pause(self):
        # Some e congela (tela cheia); guarda quais timers estavam rodando
        if getattr(self, "_paused", None) is not None: return
        self._paused = []
        for value in list(vars(self).values()):
            if isinstance(value, QTimer) and value.isActive():
                ms = value.remainingTime() if value.isSingleShot() else value.interval()
                self._paused.append((value, max(0, ms)))
                value.stop()
        self._paused_visible = self.isVisible()
        self.hide()

    def resume(self):
        if getattr(self, "_paused", None) is None: return
        for value, ms in self._paused:
            value.start(ms)
        self._paused = None
        if self._paused_visible: self.show()

    def shutdown(self):
        # Para os timers antes de fechar, senão o pet antigo continua rodando escondido
        for value in list(vars(self).values()):
            if isinstance(value, QTimer):
                value.stop()
        if self.shadow:
            self.shadow.close()
            self.shadow.deleteLater()
        self.close()
        self.deleteLater()

    def look_at_mouse(self, flip):
        """Se o mouse estiver por perto, vira para o lado dele (os desenhos olham para a direita)."""
        c = QCursor.pos()
        cx, cy = c.x() - OX, c.y() - OY
        meio = self.x + self.box / 2
        if abs(cx - meio) < 700 and abs(cy - (self.y + self.box / 2)) < 500 and abs(cx - meio) > 15:
            self.direction = 1 if cx > meio else -1
            return self.direction == -1
        return flip

    def refresh_image(self):
        # Reaplica a imagem atual (para o tom de noite mudar mesmo com o pet parado)
        if getattr(self, "_last_img", None): self.set_image(*self._last_img)

    def contextMenuEvent(self, e):
        # Botão direito em qualquer personagem: menu rápido
        if MANAGER: MANAGER.quick_menu(e.globalPos(), alvo=self)

    def move(self, *a):
        # Coordenadas do pet são do monitor escolhido; aqui vira posição real na área de trabalho
        if len(a) == 2:
            super().move(int(a[0]) + OX, int(a[1]) + OY)
        else:
            super().move(a[0])

    def update_pos(self, new_x, new_y):
        self.x = new_x
        self.y = new_y
        self.move(int(self.x), int(self.y))
        self.raise_()
        self.update_shadow()

    def update_shadow(self):
        if self.shadow_ratio is None: return
        if self.shadow is None: self.shadow = Shadow()
        if not self.isVisible():
            self.shadow.hide()
            return
        # Quanto mais alto, menor e mais clara a sombra
        alt = max(0, (self.sh - 10 - self.box) - self.y)
        f = max(0.25, 1 - alt / (self.sh * 0.7))
        w = self.box * self.shadow_ratio * f
        chao = chao_em(self.x + self.box / 2) or self.sh
        self.shadow.place(self.x + self.box / 2, chao - 10 - 3 * ESCALA, w, w * 0.2, 0.33 * f)

    def showEvent(self, e):
        super().showEvent(e)
        self.update_shadow()

    def hideEvent(self, e):
        super().hideEvent(e)
        if self.shadow: self.shadow.hide()

class Rocket(Pet):
    shadow_ratio = 0.8
    clicked = pyqtSignal()  # clique (sem arrastar) no foguete = lançar
    def __init__(self):
        screen_geo = tela_geo()
        sw, sh = screen_geo.width(), screen_geo.height()
        super().__init__("Rocket", IMG_DIR, None, random.randint(0, sw-150), 0)
        self.show_anim("rocket_parked", 0, fallback="foguete_deitado")
        # Com "lugar aleatório" desligado, volta para onde você deixou da última vez
        # (guardado como fração da largura da tela); ligado, nasce num lugar qualquer
        if not CFG["foguete_aleatorio"] and CFG.get("foguete_x") is not None:
            self.x = CFG["foguete_x"] * (sw - self.box)
        self.update_pos(max(0, min(self.x, sw - self.box)), self.ground_y)
        self.home_x, self.home_y = self.x, self.y
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.press_x = None
        self.dragging = False

        # O botão fica EM CIMA do label da imagem
        self.btn = QPushButton("🚀 LANÇAR", self)
        bw = min(60, self.box)
        self.btn.setGeometry((self.box - bw) // 2, self.box - 28, bw, 20)
        self.btn.setVisible(CFG["botao_lancar"])
        self.btn.setStyleSheet("font-size: 9px; background: yellow; border: 1px solid black; font-weight: bold; color: black;")
        self.btn.raise_() # Garante que o botão esteja acima da imagem

        # Flutua devagar para cima e para baixo (para não parecer parado/estático)
        self.float_t = random.uniform(0, 6.28)
        self.float_timer = QTimer()
        self.float_timer.timeout.connect(self.float_step)
        self.float_timer.start(50)

    def float_step(self):
        if not self.isVisible(): return
        self.float_t += 0.05 * 2 * math.pi / 3.2  # uma volta a cada ~3,2 s
        # Só move (sem raise_), senão disputa a frente com o Jimmy quando ele passa na frente
        self.y = self.home_y - (1 + math.sin(self.float_t)) * 1.5 * vel()
        self.move(int(self.x), int(self.y))
        self.update_shadow()

    def mousePressEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton: return
        self.press_x = e.globalPosition().x()
        self.press_home = self.home_x
        self.dragging = False

    def mouseMoveEvent(self, e):
        if self.press_x is None: return
        dx = e.globalPosition().x() - self.press_x
        if not self.dragging and abs(dx) < 6: return  # tremidinha da mão ainda conta como clique
        if not self.dragging:
            self.dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        # Arrastando: só anda para os lados, em cima da barra de tarefas
        self.home_x = max(0, min(self.press_home + dx, self.sw - self.box))
        self.x = self.home_x
        self.move(int(self.x), int(self.y))
        self.update_shadow()

    def mouseReleaseEvent(self, e):
        if self.press_x is None: return
        self.press_x = None
        if self.dragging:
            self.dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            CFG["foguete_x"] = self.home_x / max(1, self.sw - self.box)
            save_cfg(CFG)
        else:
            self.clicked.emit()

    def park(self):
        if CFG["foguete_aleatorio"]:
            self.home_x = random.uniform(0, self.sw - self.box)   # renasce num lugar novo
        elif CFG.get("foguete_x") is not None:
            self.home_x = CFG["foguete_x"] * (self.sw - self.box)  # sempre no lugar escolhido
        self.x = self.home_x
        self.update_pos(self.home_x, self.home_y)
        self.show()

class Jimmy(Pet):
    shadow_ratio = 0.42
    launched = pyqtSignal()
    def __init__(self, rocket):
        screen_geo = tela_geo()
        sw, sh = screen_geo.width(), screen_geo.height()
        super().__init__("Jimmy", IMG_DIR, None, random.randint(0, sw-150), 0)
        self.show_anim("jimmy_idle", 0, fallback="jimmy_idle")
        self.update_pos(self.x, self.ground_y)
        self.rocket = rocket
        self.rocket.btn.clicked.connect(self.launch_now)
        self.rocket.clicked.connect(self.launch_now)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_vx = 0.0
        self.sleep_kind = None
        self.sleep_timer = 0
        self.rem_kind = None
        self.rem_timer = 0
        self.noite_avisada = None
        self.bubble = Bubble(self.clicou_aviso)
        self.say_timer = 0
        self.show_timer = 0
        self.phase = None
        self.party_effect = None
        self.greet = False
        self.visit_friend = None
        self.visit_talking = False
        # Rajada de vento que joga ele de volta lá pra cima (a cada 5 a 15 min, sorteado)
        self.updraft = 0.0
        self.next_gust = time.time() + random.uniform(300, 900)
        self.proxima_curiosidade = time.time() + random.uniform(300, 600)
        self.guarda = None        # guarda-chuva: None, "abrindo", "aberto", "vento", "fechando"
        self.guarda_t = 0
        self.hovering = False
        self.hover_ticks = 0
        self.hover_cooldown = 0.0

        self.timer = QTimer()
        self.timer.timeout.connect(self.logic)
        self.timer.start(30)

        self.behavior_timer = QTimer()
        self.behavior_timer.timeout.connect(self.change_behavior)
        self.behavior_timer.start(3000)

        # Viagem até o foguete em tempos aleatórios de 1 a 5 minutos
        self.trip_timer = QTimer()
        self.trip_timer.setSingleShot(True)
        self.trip_timer.timeout.connect(self.go_to_rocket)
        self.schedule_trip()

        # "normal" = no chão (andando, parado ou indo até o foguete)
        self.sequence_state = "normal"
        self.state = "idle"
        self.flight_timer = 0
        self.tick = 0
        self.vx = 0.0
        self.vy = 0.0
        self.walk_dist = 0.0

    def schedule_trip(self):
        lo = max(1, int(CFG["viagem_min"]))
        hi = max(lo, int(CFG["viagem_max"]))
        self.trip_timer.start(random.randint(lo, hi) * 60 * 1000)

    def go_to_rocket(self, passeio=False, conserto=False):
        if self.sequence_state != "normal": return
        if conserto and not self.has_anim("conserta"): return
        self.trip_timer.stop()
        self.modo_passeio = passeio
        self.modo_conserto = conserto
        self.state = "going"

    def start_resgate(self, planeta):
        self.trip_timer.stop()
        self.sequence_state = "resgate"
        self.state = "idle"
        self.vx = self.vy = 0.0
        self.res = {"fase": "olha", "t": 0, "planeta": planeta, "carona": None}
        self.say(random.choice(["Olha lá em cima! Uma lhama perdida no espaço! 🦙🪐",
                                "Aquilo é... uma lhama num planeta?! 🦙🪐"]), 100)

    def resgate_logic(self):
        r, v = self.res, vel()
        r["t"] += 1
        pl = r["planeta"]
        if r["fase"] == "olha":
            self.direction = 1 if pl.cx > self.x + self.box / 2 else -1
            self.show_anim("ideia_susto", 0, flip=self.direction == -1, fallback="jimmy_idle")
            self.update_pos(self.x, self.ground_y)
            if r["t"] > 200:
                r["fase"], r["t"] = "anda", 0
                self.say("Segura aí, Carl! Eu busco! 🚀", 80)
        elif r["fase"] == "anda":
            dx = self.board_x() - self.x
            if abs(dx) <= 4 * v:
                self.rocket.hide()
                self.show_anim("voo_senta", 0)
                self.base_x, self.base_y = self.board_left(), self.ground_y
                self.update_pos(self.base_x, self.base_y)
                r["fase"], r["t"] = "decola", 0
                tocar("decolagem")
                return
            self.direction = 1 if dx > 0 else -1
            self.x += self.direction * 4 * v
            self.show_anim("jimmy_walk", r["t"] // 3, flip=self.direction == -1)
            self.update_pos(self.x, self.ground_y)
        elif r["fase"] == "decola":
            self.show_anim("voo_senta", 0)
            self.update_pos(self.base_x + random.uniform(-2, 2), self.base_y + random.uniform(-2, 2))
            if FX and r["t"] % 2 == 0:
                FX.smoke(self.base_x + self.box * random.uniform(0.1, 0.4), self.sh - 14, random.uniform(5, 9),
                         life=50, vx=random.uniform(-1.2, 1.2), vy=-0.3, gray=random.randint(190, 225), alpha=0.5, grow=2.0)
            if r["t"] > 30: r["fase"], r["t"] = "sobe", 0
        elif r["fase"] in ("sobe", "desce"):
            indo = r["fase"] == "sobe"
            # Para do lado da lhama, em cima do planeta
            tx = pl.cx - self.box * 0.85 if indo else self.base_x
            ty = max(0, pl.chao_lhama - self.box * 0.8) if indo else self.base_y
            dx, dy = tx - self.x, ty - self.y
            d = math.hypot(dx, dy)
            vel_max = 7 * v
            self.vx += (max(-vel_max, min(vel_max, dx * 0.05)) - self.vx) * 0.12
            self.vy += (max(-vel_max, min(vel_max, dy * 0.05)) - self.vy) * 0.12
            self.x += self.vx
            self.y += self.vy
            if abs(self.vx) > 0.5 * v: self.direction = 1 if self.vx > 0 else -1
            flip = self.direction == -1
            if self.has_anim("voo_brinca") and not indo:
                anim, i = "voo_brinca", (r["t"] // 45) % 5
            else:
                anim, i = "voo_monta", (2, 3, 4, 3)[(r["t"] // 10) % 4]
            self.show_anim(anim, i, flip=flip, angle=math.sin(r["t"] * 0.1) * 3)
            self.update_pos(self.x, self.y)
            if FX and r["t"] % 2 == 0:
                FX.smoke(self.x + self.box * (0.18 if not flip else 0.82), self.y + self.box * 0.85, random.uniform(3.5, 6),
                         life=35, vx=-self.direction * 0.6, vy=random.uniform(0.2, 0.8), gray=random.randint(205, 235), alpha=0.45, grow=1.8)
            if r["carona"]: r["carona"].follow(self, flip)
            if r["t"] % 10 == 0: _topmost(self)       # na frente do planeta
            if indo and d < 18 * v:
                r["fase"], r["t"] = "pega", 0
            elif not indo and (d < 10 * v or r["t"] > 900):
                self.update_pos(self.base_x, self.base_y)
                self.rocket.show()
                if r["carona"]:
                    r["carona"].close(); r["carona"].deleteLater()
                pl.sumir()
                self.sequence_state = "normal"
                self.state = "idle"
                stat("resgates")
                if MANAGER: MANAGER.fim_resgate(pl.lhama_anim)
        elif r["fase"] == "pega":
            if r["t"] == 1: _topmost(self)
            self.vx *= 0.8; self.vy *= 0.8
            self.show_anim("voo_monta", 2, flip=self.direction == -1)
            self.update_pos(self.x, self.y + math.sin(r["t"] * 0.2) * 1.5)
            if r["t"] == 25:
                pl.com_lhama = False
                pl.update()
                r["carona"] = LhamaCarona(pl.lhama_anim)
                tocar("bolinha")
                self.say("Peguei! Segura firme, lhaminha! 🦙", 70)
            if r["carona"]: r["carona"].follow(self, self.direction == -1)
            if r["t"] > 70: r["fase"], r["t"] = "desce", 0

    def start_conserto(self):
        """Manutenção no foguete: pensa, ajusta, solda (com faíscas), mexe na fiação e aperta."""
        self.modo_conserto = False
        self.rocket.hide()          # o foguete da cena já está desenhado nos quadros
        self.sequence_state = "conserto"
        self.show_timer = 0
        self.vx = 0.0
        self.show_anim("conserta", 0)
        r = self.rocket
        self.base_x = max(0, min(r.home_x + r.box / 2 - self.box / 2, self.sw - self.box))
        self.update_pos(self.base_x, self.ground_y)
        self.say(random.choice(["Hora da manutenção! 🔧", "Esse foguete precisa de uns ajustes... 🔧",
                                "Vou turbinar esse motor! 🔧⚡"]), 80)

    def conserto_logic(self):
        self.show_timer += 1
        k = self.show_timer
        passo = min(5, k // 75)
        self.show_anim("conserta", passo)
        self.update_pos(self.base_x, self.ground_y)
        if FX and passo == 2 and k % 3 == 0:
            # Solda: faíscas saindo da ponta do maçarico
            FX.sparks(self.x + self.box * 0.72, self.y + self.box * 0.55, 5,
                      colors=[(255, 240, 160), (255, 190, 60), (255, 255, 255)], speed=(1.5, 5), life=(10, 22))
        if FX and passo == 3 and k % 25 == 0:
            FX.sparks(self.x + self.box * 0.6, self.y + self.box * 0.6, 4, colors=[(120, 200, 255), (255, 255, 255)], speed=(1, 3))
        if k == 2 * 75: tocar("brainblast")
        if k >= 6 * 75:
            self.rocket.show()
            self.sequence_state = "normal"
            self.state = "idle"
            stat("consertos")
            self.say(random.choice(["Foguete novinho em folha! 🔧✨", "Pronto! Agora vai voar mais rápido! 🚀",
                                    "Neutron, você é um gênio! 😎🔧"]), 90)

    def start_passeio(self):
        """Monta no foguete e faz um voo rasante pela tela, ida e volta, e pousa no lugar."""
        self.modo_passeio = False
        self.rocket.hide()
        self.sequence_state = "passeio"
        self.show_timer = 0
        self.vx = 0.0
        self.show_anim("voo_senta", 0)
        self.base_x, self.base_y = self.board_left(), self.ground_y
        self.update_pos(self.base_x, self.base_y)
        self.pas_dir = 1 if self.base_x < self.sw / 2 else -1
        self.pas_voltas = 0
        stat("passeios")

    def passeio_logic(self):
        self.show_timer += 1
        k, v = self.show_timer, vel()
        if k == 1: tocar("decolagem")
        if k < 30:
            # Liga o motor: treme sentado, fumaça no chão
            anim, pose = "voo_senta", 0
            x, y = self.base_x + random.uniform(-2, 2), self.base_y + random.uniform(-2, 2)
            if FX and k % 2 == 0:
                FX.smoke(self.base_x + self.box * random.uniform(0.1, 0.4), self.sh - 14, random.uniform(5, 9),
                         life=50, vx=random.uniform(-1.2, 1.2), vy=-0.3, gray=random.randint(190, 225), alpha=0.5, grow=2.0)
            self.update_pos(x, y)
            self.show_anim(anim, pose, flip=self.pas_dir == -1)
            return
        altura = min(1.0, (k - 30) / 35) * 170 * v
        indo_pousar = self.pas_voltas >= 1 and abs(self.x - self.base_x) < 12 * v
        if indo_pousar or k > 1500:
            # Pousa de volta no lugar do foguete
            self.y += 3 * v
            self.x += (self.base_x - self.x) * 0.2
            if self.y >= self.base_y:
                self.update_pos(self.base_x, self.base_y)
                self.rocket.park()
                self.sequence_state = "normal"
                self.state = "idle"
                self.say("Que passeio! 😎", 80)
                return
            self.show_anim("voo_senta", 0, flip=self.pas_dir == -1)
            self.update_pos(self.x, self.y)
            return
        # Voo rasante com balanço; na borda da tela faz a curva e volta
        self.x += self.pas_dir * 6 * v
        if self.x <= 10 or self.x >= self.sw - self.box - 10:
            self.pas_dir *= -1
            self.pas_voltas += 1
            self.x = max(10, min(self.x, self.sw - self.box - 10))
        y = self.base_y - altura + math.sin(k * 0.1) * 10 * v
        if self.has_anim("voo_brinca"):
            anim, pose = "voo_brinca", (k // 45) % 5
        else:
            anim, pose = "voo_monta", (2, 3, 4, 3)[(k // 10) % 4]
        if FX:
            tail_x = self.x + self.box * (0.18 if self.pas_dir == 1 else 0.82)
            FX.smoke(tail_x, y + self.box * 0.85, random.uniform(3.5, 6), life=35, vx=-self.pas_dir * 0.6,
                     vy=random.uniform(0.2, 0.8), gray=random.randint(205, 235), alpha=0.45, grow=1.8)
        self.show_anim(anim, pose, flip=self.pas_dir == -1, angle=math.sin(k * 0.1) * 3)
        self.update_pos(self.x, y)

    @staticmethod
    def is_night():
        h = time.localtime().tm_hour
        return h >= 22 or h < 6

    def start_sleep(self, kind):
        self.guarda = None
        # "noite" = deita e dorme; "cochilo_pe" / "cochilo_sentado" = cochilo curto
        self.sequence_state = "sleeping"
        self.sleep_kind = kind
        self.sleep_timer = 0
        self.vx = 0.0
        self.trip_timer.stop()

    def say(self, text, ticks=120):
        if self.sequence_state == "reminder": return
        self.bubble.say(text)
        self.say_timer = ticks
        self.bubble.follow(self)

    def start_blast(self):
        stat("blasts")
        self.sequence_state = "blast"
        self.show_timer = 0
        self.vx = 0.0
        self.phase = "pensa"

    def start_party(self, text, effect):
        self.sequence_state = "party"
        self.show_timer = 0
        self.vx = 0.0
        self.party_effect = effect
        self.phase = "festa"
        self.say(text, 420)

    def start_visit(self, friend):
        stat("amigos")
        self.sequence_state = "visit"
        self.visit_friend = friend
        self.visit_talking = False
        self.vx = 0.0
        self.show_timer = 0

    def end_visit(self):
        self.visit_friend = None
        self.visit_talking = False
        self.say_timer = 0
        self.bubble.hide()
        if self.sequence_state == "visit":
            self.sequence_state = "normal"
            self.state = "idle"

    def end_show(self):
        # Fim do Brain Blast / festa
        self.sequence_state = "normal"
        self.state = "idle"
        self.phase = None
        self.say_timer = 0
        self.bubble.hide()

    def can_remind(self):
        return self.sequence_state == "normal" and self.state != "going" and self.isVisible()

    def start_reminder(self, kind, text=None, anim=None):
        self.sequence_state = "reminder"
        self.rem_kind = kind
        self.rem_anim = anim or "aviso_" + kind
        self.rem_timer = 0
        self.vx = 0.0
        self.bubble.say(text or AVISOS[kind])
        tocar("aviso")
        if text is None and kind in ("agua", "pausa", "comer", "exercicio"):
            stat("avisos")

    def clicou_aviso(self):
        # Clicou no balão (ou no Jimmy) durante o aviso: no aviso do canal, abre o YouTube
        if self.rem_kind == "canal":
            QDesktopServices.openUrl(QUrl(CANAL_URL))
        self.end_reminder()

    def end_reminder(self):
        if self.sequence_state != "reminder": return
        self.bubble.hide()
        kind = self.rem_kind
        self.rem_kind = None
        self.sequence_state = "normal"
        self.state = "idle"
        # Depois do aviso de dormir, ele vai deitar
        if kind == "dormir" and CFG["dormir"] and self.is_night():
            self.start_sleep("noite")

    def wake_up(self):
        if self.sequence_state != "sleeping": return
        som_loop("ronco", False)
        self.sequence_state = "waking"
        self.sleep_timer = 0

    def pause(self):
        som_loop("ronco", False)
        self.bubble.hide()
        super().pause()

    def resume(self):
        super().resume()
        if self.sequence_state == "reminder": self.bubble.follow(self)

    def shutdown(self):
        som_loop("ronco", False)
        self.bubble.close()
        self.bubble.deleteLater()
        super().shutdown()

    def mousePressEvent(self, e):
        # Clicou nele durante um lembrete: dispensa
        if e.button() == Qt.MouseButton.LeftButton and self.sequence_state == "reminder":
            self.clicou_aviso()
            return
        # Clicou nele dormindo: acorda
        if e.button() == Qt.MouseButton.LeftButton and self.sequence_state == "sleeping":
            self.wake_up()
            return
        # Clicou nele de paraquedas: sobe uma rajada de vento e joga ele de volta pra cima
        if (e.button() == Qt.MouseButton.LeftButton and self.sequence_state == "parachute"
                and self.flight_timer > 10 and self.updraft > -4 * vel()):
            self.rajada_clique()
            return
        # Pega o Jimmy com o mouse (só quando ele está no chão)
        if e.button() != Qt.MouseButton.LeftButton or self.sequence_state != "normal": return
        self.trip_timer.stop()
        self.guarda = None
        self.sequence_state = "dragged"
        self.state = "idle"
        self.flight_timer = 0
        self.vx = self.drag_vx = 0.0
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        self.show_anim("jimmy_fall", 0, anchor="center", fallback="jimmy_fall")
        gp = e.globalPosition()
        self.drag_off = (gp.x() - self.x, gp.y() - self.y)
        self.clique = (time.time(), gp.x(), gp.y(), self.x, self.y)
        self.last_drag_x = gp.x()

    def rajada_clique(self):
        v = vel()
        # Mais forte quanto mais perto do chão, mas sem passar do topo da tela
        perto = max(0.0, min(1.0, (self.y + self.box) / max(1, self.sh)))
        self.updraft = -random.uniform(8, 11) * (0.6 + perto * 0.6) * v
        self.wind = random.choice([-1, 1]) * random.uniform(1.0, 2.5)
        stat("rajadas")
        tocar("paraquedas")
        if random.random() < 0.5:
            self.say(random.choice(["Uaaaau! 🌪️", "Ei! Para com isso! 😆", "Vento de novo?! 🌬️"]), 70)
        if FX:
            # Coluna de ar subindo por baixo do Jimmy
            cx, base = self.x + self.box / 2, self.y + self.box
            for _ in range(16):
                FX.smoke(cx + random.uniform(-35, 35) * v, base + random.uniform(0, 70) * v, random.uniform(4, 8),
                         life=random.randint(25, 40), vx=random.uniform(-0.6, 0.6), vy=-random.uniform(3, 6) * v,
                         gray=random.randint(225, 250), alpha=0.35, grow=1.4)

    def mouseMoveEvent(self, e):
        if self.sequence_state != "dragged": return
        gp = e.globalPosition()
        self.drag_vx = gp.x() - self.last_drag_x
        self.last_drag_x = gp.x()
        nx = max(0, min(gp.x() - self.drag_off[0], self.sw - self.box))
        ny = max(0, min(gp.y() - self.drag_off[1], self.ground_y))
        self.update_pos(nx, ny)

    def mouseReleaseEvent(self, e):
        if self.sequence_state != "dragged": return
        t0, gx, gy, x0, y0 = self.clique
        gp = e.globalPosition()
        if time.time() - t0 < 0.4 and math.hypot(gp.x() - gx, gp.y() - gy) < 6:
            # Foi só um clique: volta para o lugar e mostra o menu
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.sequence_state = "normal"
            self.state = "idle"
            self.update_pos(x0, y0)
            self.show_anim("jimmy_idle", 0, flip=self.direction == -1)
            if MANAGER: MANAGER.menu_clique(gp.toPoint())
            return
        stat("arrastos")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        # O vento vai na direção em que ele foi "jogado"
        self.wind = max(-3.0, min(3.0, self.drag_vx * 0.3))
        if abs(self.wind) < 0.5:
            self.wind = random.choice([-1, 1]) * random.uniform(0.6, 1.2)
        self.gust = 0
        if self.ground_y - self.y > 120 * vel():
            # Solto no alto: abre o paraquedas
            self.sequence_state = "parachute"
            self.flight_timer = 10
            self.show_anim("jimmy_parachute", 0, anchor="center", fallback="jimmy_caindo_paraquedas")
            tocar("paraquedas")
        else:
            # Perto do chão: só cai
            self.sequence_state = "falling"
            self.fall_speed = 2
            self.spin = 0

    def enterEvent(self, e):
        self.hovering = True
        self.hover_ticks = 0

    def leaveEvent(self, e):
        self.hovering = False

    def start_viagem(self, pid, nome):
        lado = 1 if self.x > self.sw / 2 else -1
        self.sequence_state = "viagem"
        self.viagem = {"pid": pid, "nome": nome, "lado": lado, "fase": "indo", "t": 0, "ack": False, "fala": ""}
        self.say(f"Vou visitar o PC do {nome}! 🛰️", 80)

    def voltar_viagem(self, fala):
        v = getattr(self, "viagem", None)
        if not v or v["fase"] not in ("fora", "indo"): return
        v.update(fase="voltando", t=0, fala=fala)
        self.x = -self.box if v["lado"] == -1 else self.sw
        self.show()

    def viagem_logic(self):
        v = self.viagem
        v["t"] += 1
        k = vel()
        if v["fase"] == "indo":
            # Anda até a borda e sai da tela
            self.x += v["lado"] * 3 * k
            self.walk_dist += 3 * k
            self.show_anim("jimmy_walk", int(self.walk_dist / (7 * k)), flip=v["lado"] == -1, fallback="jimmy_walk1")
            self.update_pos(self.x, self.ground_y)
            if self.x < -self.box or self.x > self.sw:
                self.bubble.hide()
                self.say_timer = 0
                self.hide()
                v.update(fase="fora", t=0)
                if MANAGER and MANAGER.rede: MANAGER.rede.enviar({"tipo": "visita", "para": v["pid"]})
        elif v["fase"] == "fora":
            # Esperando: sem resposta em 3 s, ou passeio longo demais, ele volta
            if (not v["ack"] and v["t"] > 100) or v["t"] > 4000:
                self.voltar_viagem("Ninguém em casa... 🤷")
        elif v["fase"] == "voltando":
            self.x -= v["lado"] * 3 * k
            self.walk_dist += 3 * k
            self.show_anim("jimmy_walk", int(self.walk_dist / (7 * k)), flip=v["lado"] == 1, fallback="jimmy_walk1")
            self.update_pos(self.x, self.ground_y)
            if v["t"] > 60:
                self.sequence_state = "normal"
                self.state = "idle"
                self.say(v["fala"], 100)
                self.viagem = None

    def start_danca(self):
        stat("dancas")
        self.sequence_state = "danca"
        self.show_timer = 0
        self.vx = 0.0
        self.guarda = None

    def end_danca(self):
        if self.sequence_state == "danca":
            self.sequence_state = "normal"
            self.state = "idle"

    def start_invencao(self, tipo=None):
        g = MANAGER.goddard if MANAGER else None
        pode_raio = g is not None and not g.flying and g.isVisible()
        tipo = tipo or random.choice(["painel", "controle"] + (["raio", "raio"] if pode_raio else []))
        if tipo in ("raio", "controle") and not pode_raio:
            tipo = "painel"
        stat("invencoes")
        self.sequence_state = "invencao"
        self.inv_tipo = tipo
        self.show_timer = 0
        self.vx = 0.0

    def end_invencao(self):
        g = MANAGER.goddard if MANAGER else None
        if g and g.raio_alvo < 1: g.encolher(False)   # nunca deixa o Goddard encolhido
        if self.sequence_state == "invencao":
            self.sequence_state = "normal"
            self.state = "idle"

    def invencao_logic(self, flip):
        self.show_timer += 1
        k = self.show_timer
        g = MANAGER.goddard if MANAGER else None
        tipo = self.inv_tipo
        dx = 0
        if tipo == "painel":
            # Mexe no painel, aperta o botão, a máquina treme... e solta fumaça
            if k == 1: self.say("Hora de inventar! 🔧", 70)
            if k < 70: anim, i = "inv_painel", (k // 12) % 2
            elif k < 100: anim, i = "inv_aperta", 0
            elif k < 150:
                if k == 100: tocar("brainblast")
                anim, i = "inv_treme", 0
                dx = random.uniform(-2, 2)
            elif k < 240:
                if k == 150:
                    tocar("pouso")
                    self.say("Ops... 😅 De volta à prancheta!", 85)
                    if FX:
                        for _ in range(12):
                            FX.smoke(self.x + self.box * random.uniform(0.5, 0.8), self.y + self.box * random.uniform(0.35, 0.6),
                                     random.uniform(7, 12), life=70, vx=random.uniform(-0.5, 1.5), vy=random.uniform(-1.5, -0.3),
                                     gray=random.randint(90, 150), alpha=0.6, grow=2.0)
                anim, i = "inv_fumaca", 0
            else:
                self.end_invencao()
                return
            flip = False
        elif tipo == "raio" and g:
            # Raio encolhedor no Goddard de verdade
            flip = g.x + g.box / 2 < self.x + self.box / 2
            alvo = (g.x + g.box / 2, g.y + g.box * 0.6)
            if k == 1: self.say("Testando o raio encolhedor! 🔫", 80)
            if k < 40: anim, i = "inv_mira", 0
            elif k < 70:
                if k == 40:
                    tocar("brainblast")
                    g.encolher(True)
                if FX and k % 3 == 0:
                    FX.sparks(*alvo, 6, colors=[(120, 255, 200), (255, 255, 140)], speed=(2, 6), gravity=0.3)
                anim, i = "inv_raio", 0
            elif k < 200:
                if k == 70: self.say("Hahaha! Olha o tamanho dele! 😆", 100)
                anim, i = "inv_ri", 0
            elif k < 230: anim, i = "inv_mira", 0
            elif k < 260:
                if k == 230:
                    tocar("brainblast")
                    g.encolher(False)
                if FX and k % 3 == 0:
                    FX.sparks(*alvo, 6, colors=[(120, 255, 200), (255, 255, 140)], speed=(2, 6), gravity=0.3)
                anim, i = "inv_raio", 0
            elif k < 300:
                if k == 262: self.say("Pronto, voltou ao normal! 😅", 80)
                anim, i = "jimmy_idle", 0
            else:
                self.end_invencao()
                return
        else:
            # Óculos de cientista e controle remoto: o Goddard "obedece"
            if k == 1: self.say("Modo cientista! 🥽", 70)
            if k < 60: anim, i = "inv_oculos", 0
            elif k < 190:
                if k == 60: self.say("Goddard, pula! 🎮", 70)
                if k in (75, 115, 155) and g and not g.flying and not g.react:
                    g.start_react("jump", 26)
                anim, i = "inv_controle", 0
            else:
                self.end_invencao()
                return
        self.show_anim(anim, i, flip=flip, fallback="jimmy_idle")
        self.update_pos(self.x + dx, self.ground_y)
        self.x -= dx

    def open_umbrella(self):
        if self.guarda is None:
            self.guarda, self.guarda_t = "abrindo", 0

    def close_umbrella(self):
        if self.guarda in ("aberto", "vento", "abrindo"):
            self.guarda, self.guarda_t = "fechando", 0

    def launch_now(self):
        # Lançamento manual: some de onde está e reaparece já agarrado no foguete
        if self.sequence_state == "reminder":
            self.end_reminder()
        if self.sequence_state in ("blast", "party"):
            self.end_show()
        if self.sequence_state == "invencao":
            self.end_invencao()
        if self.sequence_state == "danca":
            self.end_danca()
        if self.sequence_state == "visit" and self.visit_friend:
            f = self.visit_friend
            self.end_visit()
            f.uau()
        if self.sequence_state in ("sleeping", "waking"):
            som_loop("ronco", False)  # acorda num susto
            self.sequence_state = "normal"
        if self.sequence_state != "normal": return
        self.trip_timer.stop()
        self.setWindowOpacity(0.0)
        self.board_rocket()

    @property
    def in_air(self):
        return self.sequence_state in ("ignition", "flying", "exploding", "parachute", "falling", "landing", "dragged")

    def board_left(self):
        # Janela da animação de agarrar o foguete, centralizada no foguete parado
        return self.rocket.home_x + (self.rocket.box - self.anim_box("voo_pendura")) / 2

    def board_x(self):
        # Onde o Jimmy precisa parar: ao lado esquerdo do foguete, onde ele aparece na animação
        return max(0, self.board_left() + self.anim_box("voo_pendura") * 0.6 - self.box / 2)

    def board_rocket(self):
        self.guarda = None
        self.sequence_state = "boarding"
        self.flight_timer = 0
        self.vx = 0
        self.direction = 1  # o foguete da folha aponta para a direita
        self.rocket.hide()
        self.show_anim("voo_pendura", 0, fallback="jimmy_subindo_foguete")
        self.base_x, self.base_y = self.board_left(), self.ground_y
        self.update_pos(self.base_x, self.base_y)

    def start_sequence(self):
        stat("lancamentos")
        self.monta_t = None
        self.sequence_state = "flying"
        self.flight_timer = 0
        self.vy = 0.0
        self.vx = 0.0
        self.launched.emit()

    def logic(self):
        try:
            self.tick += 1
            flip = self.direction == -1
            # Balão de fala rápido (Brain Blast, festa, "Voltou!")
            if self.say_timer > 0 and self.sequence_state != "reminder":
                self.say_timer -= 1
                self.bubble.follow(self)
                if self.say_timer == 0: self.bubble.hide()
            # Perspectiva no ar
            if self.sequence_state in ("flying", "exploding", "parachute", "falling", "landing", "dragged"):
                self.update_depth()
            else:
                self.depth = 1.0

            if self.sequence_state == "normal" and self.guarda in ("abrindo", "fechando", "vento"):
                # Guarda-chuva: para no lugar enquanto abre, fecha ou briga com o vento
                self.guarda_t += 1
                k = self.guarda_t
                if self.guarda == "abrindo":
                    anim, i = ("chuva_percebe", 0) if k < 20 else ("chuva_abre", min((k - 20) // 10, 1))
                    if k > 42: self.guarda = "aberto"
                elif self.guarda == "fechando":
                    anim, i = "chuva_fecha", min(k // 14, 1)
                    if k > 30: self.guarda = None
                else:
                    anim, i = "chuva_vento", (k // 8) % 2
                    if k > 45: self.guarda = "aberto"
                self.vx *= 0.8
                self.show_anim(anim, i, flip=flip, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)
                return

            if self.sequence_state == "normal":
                # Com o guarda-chuva aberto, de vez em quando vem um vento
                if self.guarda == "aberto" and random.random() < 0.001:
                    self.guarda, self.guarda_t = "vento", 0
                    return   # no próximo quadro já mostra a briga com o vento
                # Mouse parado em cima dele: solta uma frase
                if self.hovering and self.say_timer == 0 and CFG["frases"] and not quieto():
                    self.hover_ticks += 1
                    if self.hover_ticks == 25 and time.time() > self.hover_cooldown:
                        self.say(random.choice(FRASES), 100)
                        self.hover_cooldown = time.time() + 12
                # Velocidade alvo conforme o que ele está fazendo; acelera e freia suave
                target = 0.0
                v = vel()
                if self.state == "going":
                    dx = self.board_x() - self.x
                    if abs(dx) <= max(2, 6 * v) and abs(self.vx) < 1.5 * v:
                        if getattr(self, "modo_conserto", False):
                            self.start_conserto()
                        elif getattr(self, "modo_passeio", False):
                            self.start_passeio()
                        else:
                            self.board_rocket()
                        return
                    self.direction = 1 if dx > 0 else -1
                    target = min(3.5 * v, abs(dx) / 12 + 0.6 * v)
                elif self.state == "walking":
                    target = 2.0 * v
                    if (self.x <= 0 and self.direction < 0) or (self.x >= self.sw - self.box and self.direction > 0):
                        self.direction *= -1
                self.vx += (self.direction * target - self.vx) * 0.12
                self.x = max(0, min(self.x + self.vx, self.sw - self.box))
                self.walk_dist += abs(self.vx)
                if abs(self.vx) > 0.35 * v:
                    # O quadro avança pela distância andada: o pé não "patina" no chão
                    if self.guarda == "aberto":
                        self.show_anim("chuva_anda", int(self.walk_dist / (12 * v)), flip=self.vx < 0, fallback="jimmy_walk1")
                    else:
                        self.show_anim("jimmy_walk", int(self.walk_dist / (7 * v)), flip=self.vx < 0, fallback="jimmy_walk1")
                else:
                    # Parado: vira para o lado do mouse e de vez em quando troca de pose
                    flip = self.look_at_mouse(flip)
                    if self.guarda == "aberto":
                        self.show_anim("chuva_parado", 0, flip=flip, fallback="jimmy_idle")
                    else:
                        self.show_anim("jimmy_idle", 1 if self.tick % 160 < 12 else 0, flip=flip, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "sleeping":
                self.sleep_timer += 1
                k = self.sleep_timer
                if self.sleep_kind == "noite":
                    if k < 75:
                        # Esfrega o olho, boceja e se espreguiça
                        anim, i = "jimmy_yawn", min(k // 15, 4)
                    elif k < 100:
                        anim, i = "jimmy_lie", 0
                    else:
                        # Dormindo: respiração lenta com os "Zzz" mudando
                        anim, i = "jimmy_sleep", (k - 100) // 18
                        som_loop("ronco", True)
                elif self.sleep_kind == "cochilo_pe":
                    anim, i = "jimmy_doze_stand", k // 28
                    if k > 330: self.wake_up()
                else:
                    anim, i = ("jimmy_yawn", 1) if k < 30 else ("jimmy_doze_sit", (k - 30) // 22)
                    # "ausente" (você saiu do PC) só acorda quando você voltar ou clicar
                    if k > 400 and self.sleep_kind != "ausente": self.wake_up()
                self.show_anim(anim, i, flip=flip, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "waking":
                # Acordando: espreguiça, esfrega o olho e volta ao normal
                self.sleep_timer += 1
                k = self.sleep_timer
                if k < 14:
                    self.show_anim("jimmy_yawn", 4, flip=flip, fallback="jimmy_idle")
                elif k < 28:
                    self.show_anim("jimmy_yawn", 0, flip=flip, fallback="jimmy_idle")
                else:
                    self.sequence_state = "normal"
                    self.state = "idle"
                    self.sleep_kind = None
                    self.show_anim("jimmy_idle", 0, flip=flip, fallback="jimmy_idle")
                    self.schedule_trip()
                    if self.greet:
                        self.greet = False
                        self.say("Voltou! 👋", 110)
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "passeio":
                self.passeio_logic()

            elif self.sequence_state == "conserto":
                self.conserto_logic()

            elif self.sequence_state == "resgate":
                self.resgate_logic()

            elif self.sequence_state == "busca_mouse":
                # Teve a ideia (lâmpada) e depois fica olhando o Goddard buscar o ponteiro
                self.busca_t += 1
                self.vx = 0.0
                c = QCursor.pos()
                alvo = (c.x() - OX) if self.busca_t < 110 else (MANAGER.goddard.x if MANAGER and MANAGER.goddard else c.x() - OX)
                self.direction = 1 if alvo > self.x + self.box / 2 else -1
                if self.busca_t < 110:
                    self.show_anim("ideia_ideia", min(5, self.busca_t // 12), flip=self.direction == -1, fallback="jimmy_idle")
                else:
                    self.show_anim("jimmy_idle", 0, flip=self.direction == -1)
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "viagem":
                self.viagem_logic()

            elif self.sequence_state == "danca":
                self.show_timer += 1
                if self.show_timer == 1: self.say("🎵 Essa música é boa!", 80)
                self.show_anim("jimmy_danca", self.show_timer // 9, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "invencao":
                self.invencao_logic(flip)

            elif self.sequence_state == "visit":
                # Conversando com um amigo: de frente para ele, gesticula quando fala
                self.show_timer += 1
                f = self.visit_friend
                if f is None:
                    self.end_visit()
                    return
                olha_esq = f.x < self.x
                if self.visit_talking and (self.show_timer // 12) % 2:
                    self.show_anim("ideia_ideia", 0, flip=olha_esq, fallback="jimmy_idle")
                else:
                    self.show_anim("jimmy_idle", 0, flip=olha_esq, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "blast":
                # Brain Blast: pensa, faísca, susto, BLAST, feliz, ideia
                self.show_timer += 1
                k = self.show_timer
                if k < 20:
                    anim, i = "ideia_vira", 0
                elif k < 110:
                    if k == 20: self.say("Pensa, pensa, pensa... 🤔", 90)
                    anim, i = "ideia_pensa", (k - 20) // 12
                elif k < 155:
                    if k == 110: tocar("brainblast")
                    anim, i = "ideia_faisca", (k - 110) // 8
                elif k < 170:
                    anim, i = "ideia_susto", 0
                elif k < 230:
                    if k == 170:
                        self.phase = "blast"
                        self.say("BRAIN BLAST! ⚡", 60)
                    anim, i = "ideia_blast", (k - 170) // 4
                    if FX and k % 4 == 0:
                        FX.sparks(self.x + self.box / 2, self.y + self.box * 0.22, 8,
                                  colors=[(120, 230, 255), (255, 240, 120), (255, 255, 255)], speed=(3, 8), gravity=0.4)
                elif k < 260:
                    self.phase = "feliz"
                    anim, i = "ideia_feliz", (k - 230) // 10
                elif k < 380:
                    if k == 260:
                        self.say(random.choice(IDEIAS), 120)
                        tocar("aviso")
                    anim, i = "ideia_ideia", (k - 260) // 20
                else:
                    self.end_show()
                    return
                self.show_anim(anim, i, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)

            elif self.sequence_state == "party":
                # Data comemorativa: pula de alegria com efeitos
                self.show_timer += 1
                k = self.show_timer
                hop = abs(math.sin(k * 0.12)) * 18 * vel()
                self.show_anim("ideia_feliz", k // 10, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y - hop)
                if FX:
                    cx = self.x + self.box / 2
                    eff = self.party_effect
                    if eff == "fogos":
                        if k % 35 == 1:
                            fx_x = cx + random.uniform(-450, 450)
                            fx_y = random.uniform(self.sh * 0.12, self.sh * 0.45)
                            cor = random.choice([(255, 80, 80), (80, 200, 255), (255, 220, 60), (160, 255, 120), (255, 120, 255)])
                            FX.sparks(fx_x, fx_y, 90, colors=[cor, (255, 255, 255)], speed=(3, 11), life=(45, 75), gravity=0.3)
                            tocar("fogos")
                    elif k % 6 == 0:
                        top = max(0, self.y - 300)
                        if eff == "natal":
                            FX.snow(cx - 500, cx + 500, top, 4)
                            FX.confetti(cx - 300, cx + 300, top, 2, [(220, 30, 30), (30, 160, 60), (255, 215, 0)])
                        elif eff == "halloween":
                            FX.confetti(cx - 400, cx + 400, top, 5, [(255, 140, 0), (130, 50, 180), (40, 40, 40)])
                        else:
                            FX.confetti(cx - 400, cx + 400, top, 5, [(255, 80, 80), (80, 200, 255), (255, 220, 60),
                                                                     (160, 255, 120), (255, 120, 255)])
                if k > 420:
                    self.end_show()

            elif self.sequence_state == "reminder":
                # Faz as poses do lembrete com o balão em cima (some sozinho em ~20 s)
                self.rem_timer += 1
                self.show_anim(self.rem_anim, self.rem_timer // 40, fallback="jimmy_idle")
                self.update_pos(self.x, self.ground_y)
                self.bubble.follow(self)
                if self.rem_timer > 660:
                    self.end_reminder()

            elif self.sequence_state == "dragged":
                # Pendurado no mouse, se debatendo e balançando com o movimento
                self.flight_timer += 1
                self.drag_vx *= 0.85
                self.show_anim("jimmy_fall", self.flight_timer // 4, flip=flip,
                               angle=max(-25, min(25, -self.drag_vx * 2)), anchor="center", fallback="jimmy_fall")

            elif self.sequence_state == "boarding":
                # Agarra o foguete (no lançamento manual, vai aparecendo aos poucos)
                self.flight_timer += 1
                if self.windowOpacity() < 1:
                    self.setWindowOpacity(min(1.0, self.flight_timer / 8))
                self.show_anim("voo_pendura", 0, fallback="jimmy_subindo_foguete")
                if self.flight_timer > 40:
                    self.sequence_state = "ignition"
                    self.flight_timer = 0
                    tocar("decolagem")

            elif self.sequence_state == "ignition":
                # Foguete começa a tremer com o Jimmy agarrado
                self.flight_timer += 1
                self.show_anim("voo_pendura", 0, fallback="jimmy_subindo_foguete")
                shake = min(3.0, self.flight_timer / 10)
                # Fumaça se espalhando no chão em volta da cauda
                if FX and self.flight_timer % 2 == 0:
                    FX.smoke(self.base_x + self.box * random.uniform(0.1, 0.4), self.sh - 14,
                             random.uniform(6, 10), life=55, vx=random.uniform(-1.5, 1.5), vy=-0.3,
                             gray=random.randint(190, 225), alpha=0.5, grow=2.2)
                self.update_pos(self.base_x + random.uniform(-shake, shake), self.base_y + random.uniform(-shake, shake))
                if self.flight_timer > 35:
                    self.update_pos(self.base_x, self.base_y)
                    self.start_sequence()

            elif self.sequence_state == "flying":
                self.flight_timer += 1
                # Sobe acelerando com o Jimmy pendurado, ganhando velocidade para o lado aos poucos
                f = vel_foguete()
                self.vy = min(self.vy + 0.3 * f, 14 * f)
                self.vx = min(self.vx + 0.1 * f, 5 * f)
                self.y -= self.vy
                self.x += self.direction * self.vx
                if self.x <= 0 or self.x >= self.sw - self.box:
                    self.direction *= -1
                    self.x = max(0, min(self.x, self.sw - self.box))
                wobble = math.sin(self.flight_timer * 0.5) * 2
                # Rastro de fumaça saindo da cauda (embaixo à esquerda quando sobe para a direita)
                if FX:
                    tail_x = self.x + self.box * (0.18 if self.direction == 1 else 0.82)
                    FX.smoke(tail_x + random.uniform(-3, 3), self.y + self.box * 0.88, random.uniform(4, 7),
                             life=45, vx=-self.direction * random.uniform(0.2, 1.0), vy=random.uniform(0.5, 1.5),
                             gray=random.randint(200, 235), alpha=0.5, grow=2.0)
                ft = self.flight_timer
                # Fases pela altura já subida (funciona em qualquer tamanho de tela)
                subida = max(0.0, min(1.0, (self.base_y - self.y) / max(1.0, self.base_y - 10)))
                if subida < 0.2:
                    # Decola pendurado, se debatendo
                    anim, pose = "voo_pendura", (ft // 10) % 2
                    wobble += math.sin(ft * 0.12) * 4
                elif subida < 0.32:
                    anim, pose = "voo_escala", 0     # escala o foguete
                elif subida < 0.42:
                    anim, pose = "voo_senta", 0      # senta
                else:
                    # Montado: do medo ao cabelo esvoaçando, depois vai e volta nas poses de vento
                    if not hasattr(self, "monta_t") or self.monta_t is None: self.monta_t = ft
                    k = (ft - self.monta_t) // 10
                    anim, pose = "voo_monta", (k if k < 4 else (2, 3, 4, 3)[(k - 4) % 4])
                    wobble += math.sin(ft * 0.08) * 2
                self.show_anim(anim, pose, flip=(self.direction == -1),
                               angle=wobble, fallback="rocket_subindo")
                if self.y <= 10:
                    self.y = 10
                    self.sequence_state = "exploding"
                    self.flight_timer = 0
                    tocar("explosao")
                    if FX:
                        cx, cy = self.x + self.box / 2, self.y + self.box / 2
                        FX.sparks(cx, cy, 45)
                        for _ in range(10):
                            FX.smoke(cx + random.uniform(-20, 20), cy + random.uniform(-20, 20), random.uniform(8, 14),
                                     life=60, vx=random.uniform(-1.5, 1.5), vy=random.uniform(-1.5, 0.5),
                                     gray=random.randint(70, 120), alpha=0.55, grow=1.8)
                self.update_pos(self.x, self.y)

            elif self.sequence_state == "exploding":
                self.flight_timer += 1
                n = self.flight_timer // 5
                if n < 3:
                    self.show_anim("rocket_explode", n, flip=flip, anchor="center", fallback="rocket__explodiu")
                    self.update_pos(self.x + random.uniform(-3, 3), self.y + random.uniform(-3, 3))
                elif self.flight_timer < 30:
                    # Fumaça se dissipando
                    self.setWindowOpacity(max(0.0, 1 - (self.flight_timer - 15) / 15))
                else:
                    # Jimmy surge da fumaça já de paraquedas
                    self.show_anim("jimmy_parachute", 0, anchor="center", fallback="jimmy_caindo_paraquedas")
                    self.sequence_state = "parachute"
                    tocar("paraquedas")
                    self.flight_timer = 0
                    self.wind = random.choice([-1, 1]) * random.uniform(0.8, 2.2)
                    self.gust = 0

            elif self.sequence_state == "parachute":
                self.flight_timer += 1
                if self.flight_timer <= 10:
                    self.setWindowOpacity(self.flight_timer / 10)
                # Rajadas de vento de vez em quando
                if random.random() < 0.01:
                    self.gust = random.uniform(-1.5, 1.5)
                self.gust *= 0.98
                wind = self.wind + self.gust
                # Balanço de pêndulo do paraquedas + inclinação a favor do vento
                swing = math.sin(self.flight_timer * 0.08)
                # Rajada surpresa: quase pousando, o vento joga ele de volta lá pra cima
                if (self.updraft == 0 and time.time() >= self.next_gust
                        and self.y > self.ground_y - 200 * vel()):
                    self.updraft = -random.uniform(12, 16) * vel()
                    self.next_gust = time.time() + random.uniform(300, 900)
                    self.wind = random.choice([-1, 1]) * random.uniform(1.5, 3.0)
                    self.say("Uaaaau! 🌪️", 80)
                    stat("rajadas")
                    tocar("paraquedas")
                if self.updraft < 0:
                    swing *= 1.8   # balança muito mais no vento forte
                angle = swing * 14 + wind * 4
                self.x += wind + swing * 1.2
                if self.updraft < 0:
                    self.y = max(10, self.y + self.updraft)
                    self.updraft = min(0.0, self.updraft + 0.16 * vel())   # vai perdendo força
                else:
                    self.y += 2 + abs(swing) * 0.6
                # Vento bate na borda da tela e vira
                if self.x <= 0 or self.x >= self.sw - self.box:
                    self.wind = -self.wind
                    self.gust = 0
                self.x = max(0, min(self.x, self.sw - self.box))
                self.show_anim("jimmy_parachute", 0 if swing >= 0 else 1, flip=flip, angle=angle,
                               anchor="center", fallback="jimmy_caindo_paraquedas")
                # Perto da barra de tarefas solta o paraquedas e só cai
                if self.y >= self.ground_y - 110 * vel():
                    self.setWindowOpacity(1.0)
                    self.sequence_state = "falling"
                    self.fall_speed = 3
                    self.spin = angle * 0.5
                self.update_pos(self.x, self.y)

            elif self.sequence_state == "falling":
                # Cai acelerando, debatendo os braços, levado pelo vento e girando para o lado
                self.fall_speed = min(self.fall_speed + 1.2, 18)
                self.y += self.fall_speed
                self.x = max(0, min(self.x + self.wind * 1.5, self.sw - self.box))
                self.spin += self.wind * 1.5
                self.show_anim("jimmy_fall", self.tick // 4, flip=flip, angle=self.spin,
                               anchor="center", fallback="jimmy_fall")
                if self.y >= self.ground_y:
                    # Bate no chão e quica uma vez
                    self.y = self.ground_y
                    self.vy = -self.fall_speed * 0.35
                    self.sequence_state = "landing"
                    tocar("pouso")
                self.update_pos(self.x, self.y)

            elif self.sequence_state == "landing":
                self.vy += 1.2
                self.y += self.vy
                self.spin *= 0.7
                self.x = max(0, min(self.x + self.wind * 0.5, self.sw - self.box))
                self.show_anim("jimmy_fall", 0, flip=flip, angle=self.spin, fallback="jimmy_fall")
                if self.y >= self.ground_y and self.vy > 0:
                    self.reset_after_fall()
                    return
                self.update_pos(self.x, self.y)

        except Exception as e: log_error(e)

    def reset_after_fall(self):
        self.sequence_state = "normal"
        self.state = "idle"
        self.vx = 0.0
        self.setWindowOpacity(1.0)
        self.show_anim("jimmy_idle", 0, flip=(self.direction == -1), fallback="jimmy_idle")
        self.update_pos(max(0, min(self.x, self.sw - self.box)), self.ground_y)
        self.rocket.park()
        self.schedule_trip()

    def change_behavior(self):
        # Amanheceu (ou desligaram o sono): acorda
        if self.sequence_state == "sleeping" and self.sleep_kind == "noite" \
                and not (CFG["dormir"] and self.is_night()):
            self.wake_up()
            return
        if self.sequence_state != "normal" or self.state == "going": return
        if self.is_night():
            # Uma vez por noite avisa que é hora de dormir (a noite conta a partir das 22h)
            noite = time.strftime("%Y-%m-%d", time.localtime(time.time() - 6 * 3600))
            if CFG["avisos"] and CFG["aviso_dormir"] and self.noite_avisada != noite:
                self.noite_avisada = noite
                self.start_reminder("dormir")
                return
            if CFG["dormir"]:
                self.start_sleep("noite")
                return
        if CFG["curiosidades"] and not quieto() and time.time() >= self.proxima_curiosidade:
            # Curiosidade de ciência (a cada 8 a 15 min)
            self.proxima_curiosidade = time.time() + random.uniform(480, 900)
            MANAGER.queue.append(("curiosidade", "🔬 " + random.choice(CURIOSIDADES), "ideia_ideia", False))
            return
        if CFG["passeios"] and not quieto() and random.random() < 0.004:   # passeio (~1 a cada 12 min)
            self.go_to_rocket(passeio=True)
            return
        if CFG["consertos"] and not quieto() and random.random() < 0.003:  # manutenção (~1 a cada 15 min)
            self.go_to_rocket(conserto=True)
            return
        if CFG["ideias"] and not quieto() and random.random() < 0.006:  # Brain Blast de vez em quando (~1 a cada 8 min)
            self.start_blast()
            return
        if CFG["invencoes"] and not quieto() and random.random() < 0.005:  # invenção (~1 a cada 10 min)
            self.start_invencao()
            return
        if CFG["dormir"]:
            if random.random() < 0.012:  # cochilo de vez em quando (~1 a cada 4 min)
                self.start_sleep(random.choice(["cochilo_pe", "cochilo_sentado"]))
                return
        self.state = random.choice(["walking", "walking", "idle"])
        if random.random() < 0.3:
            self.direction *= -1

class Friend(Pet):
    """Amigo do Jimmy que chega andando, conversa e vai embora."""
    shadow_ratio = 0.42

    def __init__(self, nome, jimmy, on_done):
        screen_geo = tela_geo()
        super().__init__(nome, IMG_DIR, None, 0, 0)
        self.key = nome
        self.jimmy = jimmy
        self.on_done = on_done
        self.show_anim(self.anim("parado"), 0)
        # Entra pelo lado da tela mais perto do Jimmy... ou pelo outro, tanto faz: sorteia
        self.side = random.choice([-1, 1])        # -1 = vem da esquerda
        self.x = -self.box if self.side == -1 else self.sw
        self.direction = -self.side                # anda em direção ao centro
        self.update_pos(self.x, self.ground_y)
        self.state = "chegando"
        self.walk_dist = 0.0
        self.line = 0
        self.line_timer = 0
        self.script = self.criar_script(nome)
        self.correndo = random.random() < 0.35 and self.has_anim(self.anim("corre"))
        self.uau_timer = 0
        self.bubble = Bubble(lambda: None)
        self.timer = QTimer()
        self.timer.timeout.connect(self.logic)
        self.timer.start(30)

    def criar_script(self, nome):
        return random.choice(CONVERSAS[nome])

    def anim(self, kind):
        return f"amigo_{self.key}_{kind}"

    def target_x(self):
        j = self.jimmy
        return j.x + j.box / 2 + self.side * 115 * vel() - self.box / 2

    def uau(self):
        # O Jimmy lançou o foguete no meio da conversa: pula de empolgação e depois vai embora
        self.state = "uau"
        self.uau_timer = 0
        self.bubble.say("Uau! Boa viagem! 🚀")
        self.bubble.follow(self)

    def leave(self):
        if self.state == "saindo": return
        # Às vezes vai embora correndo
        self.correndo = random.random() < 0.4 and self.has_anim(self.anim("corre"))
        self.state = "saindo"
        self.bubble.hide()
        self.direction = self.side                 # volta pelo mesmo lado
        if self.jimmy.sequence_state == "visit" and self.jimmy.visit_friend is self:
            self.jimmy.end_visit()

    def shutdown(self):
        self.bubble.close()
        self.bubble.deleteLater()
        super().shutdown()

    def pause(self):
        self.bubble.hide()
        super().pause()

    def logic(self):
        try:
            v = vel()
            if self.state == "uau":
                self.uau_timer += 1
                anim = self.anim("pula") if self.has_anim(self.anim("pula")) else self.anim("acena")
                self.show_anim(anim, self.uau_timer // 8, flip=self.jimmy.x < self.x)
                self.update_pos(self.x, self.ground_y)
                if self.bubble.isVisible(): self.bubble.follow(self)
                if self.uau_timer > 45:
                    self.leave()
                return
            if self.state in ("chegando", "saindo"):
                if self.state == "chegando":
                    dx = self.target_x() - self.x
                    if abs(dx) < 4 * v:
                        self.state = "conversa"
                        self.line = self.line_timer = 0
                        self.jimmy.start_visit(self)
                        return
                    self.direction = 1 if dx > 0 else -1
                vmax = (5.5 if self.correndo else 2.6) * v
                step = min(vmax, abs(dx)) if self.state == "chegando" else (6 if self.correndo else 3) * v
                self.x += self.direction * step
                self.walk_dist += step
                bob = abs(math.sin(self.walk_dist * 0.2 / v)) * 3 * v
                if self.correndo:
                    self.show_anim(self.anim("corre"), int(self.walk_dist / (16 * v)), flip=self.direction == -1)
                else:
                    self.show_anim(self.anim("anda"), int(self.walk_dist / (9 * v)), flip=self.direction == -1)
                self.update_pos(self.x, self.ground_y - bob)
                if self.state == "saindo" and (self.x < -self.box - 5 or self.x > self.sw + 5):
                    self.timer.stop()
                    self.on_done(self)
                    self.shutdown()
                return
            # Conversa
            who, text = self.script[self.line]
            ticks = int(60 + len(text) * 2.5)
            if self.line_timer == 0:
                if who == "amigo":
                    self.jimmy.say_timer = 0
                    self.jimmy.bubble.hide()
                    self.bubble.say(text)
                    self.bubble.follow(self)
                else:
                    self.bubble.hide()
                    self.jimmy.say(text, ticks)
                self.jimmy.visit_talking = who == "jimmy"
            self.line_timer += 1
            # Vira para o Jimmy
            face_right = self.jimmy.x > self.x
            engracado = any(w in text for w in ("Haha", "haha", "😅"))
            empolgado = any(w in text for w in ("ULTRA", "🛸", "🤩", "Uau", "JIMMY!"))
            debochado = any(w in text for w in ("Hmpf", "🙄", "😤"))
            if who == "amigo" and "eutron" in text and self.has_anim(self.anim("aponta")):
                img = (self.anim("aponta"), 0)                       # "Neutron!" apontando
            elif who == "amigo" and debochado and self.has_anim(self.anim("ri")) and self.key == "cindy":
                img = (self.anim("ri"), 0)                           # cara de deboche
            elif self.line in (0, len(self.script) - 1) and who == "amigo" and not empolgado:
                img = (self.anim("acena"), self.line_timer // 12)
            elif engracado and self.has_anim(self.anim("ri")):
                img = (self.anim("ri"), self.line_timer // 10)      # ri das piadas (dele ou do Jimmy)
            elif who == "amigo" and empolgado and self.has_anim(self.anim("pula")):
                img = (self.anim("pula"), self.line_timer // 8)     # pula de empolgação
            elif who == "amigo":
                img = (self.anim("fala"), self.line_timer // 9)
            else:
                img = (self.anim("parado"), 0)
            self.show_anim(img[0], img[1], flip=not face_right)
            self.update_pos(self.x, self.ground_y)
            if self.bubble.isVisible(): self.bubble.follow(self)
            if self.line_timer > ticks:
                self.line += 1
                self.line_timer = 0
                if self.line >= len(self.script):
                    self.leave()
        except Exception as e: log_error(e)

class Runner(Pet):
    """Atravessa a tela correndo (lhama fugindo, Carl atrás) e some do outro lado."""
    shadow_ratio = 0.5

    def __init__(self, anim, direction, speed, fala=None, on_done=None):
        super().__init__(anim, IMG_DIR, None, 0, 0)
        self.anim = anim
        self.direction = direction
        self.speed = speed
        self.fala = fala
        self.on_done = on_done
        self.show_anim(anim, 0, flip=direction == -1)
        self.x = -self.box if direction == 1 else self.sw
        self.update_pos(self.x, self.ground_y)
        self.dist = 0.0
        self.passou_jimmy = self.passou_goddard = False
        self.bubble = Bubble(lambda: None) if fala else None
        self.timer = QTimer()
        self.timer.timeout.connect(self.logic)
        self.timer.start(30)

    def logic(self):
        try:
            v = vel()
            self.x += self.direction * self.speed * v
            self.dist += self.speed * v
            bob = abs(math.sin(self.dist * 0.15 / v)) * 5 * v
            self.show_anim(self.anim, int(self.dist / (14 * v)), flip=self.direction == -1)
            self.update_pos(self.x, self.ground_y - bob)
            # Grita ao entrar na tela
            if self.bubble:
                if 0 < self.x < self.sw - self.box and not self.bubble.isVisible() and self.dist < 400 * v:
                    self.bubble.say(self.fala)
                if self.bubble.isVisible():
                    self.bubble.follow(self)
                    if self.dist > 700 * v: self.bubble.hide()
            m = MANAGER
            meio = self.x + self.box / 2
            if m and m.jimmy and not self.passou_jimmy and abs(meio - (m.jimmy.x + m.jimmy.box / 2)) < 60:
                self.passou_jimmy = True
                if self.bubble and m.jimmy.sequence_state == "normal" and m.jimmy.say_timer == 0:
                    m.jimmy.say(random.choice(["De novo, Carl? 🙄", "As lhamas fugiram outra vez! 🦙", "Corre, Carl! 😂"]), 90)
            if m and m.goddard and not self.passou_goddard and abs(meio - (m.goddard.x + m.goddard.box / 2)) < 80:
                self.passou_goddard = True
                if not self.bubble and not m.goddard.flying and not m.goddard.react:
                    m.goddard.start_react("bark", 30)   # late para a lhama
            if self.x < -self.box - 10 or self.x > self.sw + 10:
                self.timer.stop()
                if self.on_done: self.on_done(self)
                self.shutdown()
        except Exception as e: log_error(e)

    def shutdown(self):
        if self.bubble:
            self.bubble.close()
            self.bubble.deleteLater()
        super().shutdown()

    def pause(self):
        if self.bubble: self.bubble.hide()
        super().pause()

class CarlResgate(Pet):
    """O Carl chega desesperado, espera o Jimmy buscar a lhama no planeta e vai embora feliz com ela."""
    shadow_ratio = 0.42

    def __init__(self, jimmy, on_done):
        super().__init__("carl", IMG_DIR, None, 0, 0)
        self.jimmy = jimmy
        self.on_done = on_done
        self.show_anim("amigo_carl_corre", 0, fallback="amigo_carl_anda")
        self.side = 1 if jimmy.x + jimmy.box / 2 < self.sw / 2 else -1     # entra pelo lado com mais espaço
        self.x = self.sw if self.side == 1 else -self.box
        self.direction = -self.side
        self.alvo = max(0, min(jimmy.x + jimmy.box / 2 + self.side * 130 * vel() - self.box / 2, self.sw - self.box))
        self.update_pos(self.x, self.ground_y)
        self.state, self.t, self.dist, self.fala_t = "chegando", 0, 0.0, 0
        self.bubble = Bubble(lambda: None)
        self.timer = QTimer()
        self.timer.timeout.connect(self.logic)
        self.timer.start(30)

    def falar(self, texto, ticks=120):
        self.bubble.say(texto)
        self.fala_t = ticks

    def feliz(self):
        self.state, self.t = "feliz", 0
        self.direction = -self.side
        self.falar(random.choice(["Lhaminha!! Valeu, Jimmy! 🦙💕", "Você é o melhor, Jimmy! 🦙✨", "Nunca mais foge, tá? 🦙😭"]), 110)

    def logic(self):
        try:
            v = vel()
            self.t += 1
            hop = 0
            if self.state == "chegando":
                passo = 6 * v
                if abs(self.alvo - self.x) <= passo:
                    self.x = self.alvo
                    self.state, self.t = "esperando", 0
                    self.falar(random.choice(["Jimmy! Minha lhama foi parar naquele planeta! 😱🦙",
                                              "Socorro! A lhama tá no espaço! 🦙🪐"]), 130)
                else:
                    self.x += passo if self.alvo > self.x else -passo
                    self.dist += passo
                anim, i = "amigo_carl_corre", int(self.dist / (14 * v))
            elif self.state == "esperando":
                # Torcendo lá de baixo, olhando para o Jimmy
                j = self.jimmy
                self.direction = 1 if j.x + j.box / 2 > self.x + self.box / 2 else -1
                anim, i = ("carl_panico", self.t // 10) if self.t < 150 else ("amigo_carl_parado", 0)
                if self.t == 260: self.falar(random.choice(["Vai, Jimmy! 🙏", "Cuidado com a lhama! 🦙"]), 90)
            elif self.state == "feliz":
                anim, i = "amigo_carl_pula", self.t // 8
                hop = abs(math.sin(self.t * 0.15)) * 14 * v
                if self.t > 100: self.state, self.direction = "saindo", self.side
            else:
                self.x += self.side * 6 * v
                self.dist += 6 * v
                anim, i = "amigo_carl_corre", int(self.dist / (14 * v))
                if self.x < -self.box - 10 or self.x > self.sw + 10:
                    self.timer.stop()
                    self.on_done()
                    self.shutdown()
                    return
            self.show_anim(anim, i, flip=self.direction == -1, fallback="amigo_carl_parado")
            self.update_pos(self.x, self.ground_y - hop)
            if self.fala_t > 0:
                self.fala_t -= 1
                self.bubble.follow(self)
                if self.fala_t == 0: self.bubble.hide()
        except Exception as e:
            log_error(e)

    def shutdown(self):
        self.bubble.close()
        self.bubble.deleteLater()
        super().shutdown()

    def pause(self):
        self.bubble.hide()
        super().pause()


class Visitante(Friend):
    """Um Jimmy que veio de outro PC da rede."""
    origem_nome = "?"
    ANIMS = {"anda": "jimmy_walk", "corre": "jimmy_walk", "parado": "jimmy_idle", "fala": "ideia_ideia",
             "acena": "ideia_feliz", "pula": "ideia_feliz", "ri": "inv_ri"}

    def criar_script(self, nome):
        n = Visitante.origem_nome
        return random.choice([
            [("amigo", f"Oi! Vim do PC do {n}! 👋"), ("jimmy", "Um Jimmy de outro PC?! 😮"),
             ("amigo", "Lá também tem foguete! 🚀"), ("jimmy", "Ciência de rede! 📡"), ("amigo", "Tenho que voltar. Tchau!")],
            [("amigo", f"E aí! Sou o Jimmy do {n}! 🛰️"), ("jimmy", "Uau, viajou pelo cabo de rede?"),
             ("amigo", "Pelo Wi-Fi, é mais rápido! 😎"), ("jimmy", "Hahaha!"), ("amigo", "Até a próxima visita! 👋")],
        ])

    def anim(self, kind):
        return self.ANIMS.get(kind, "jimmy_idle")

class Goddard(Pet):
    shadow_ratio = 0.62
    def __init__(self, target):
        screen_geo = tela_geo()
        super().__init__("Goddard", IMG_DIR, None, 0, screen_geo.height()-160)
        self.show_anim("goddard_idle", 0, fallback="goddard_idle")
        self.update_pos(self.x, self.ground_y)
        self.target = target
        self.target.launched.connect(self.on_launch)
        self.timer = QTimer()
        self.timer.timeout.connect(self.follow_logic)
        self.timer.start(30)
        self.running_fast = False
        self.idle_timer = 0
        self.idle_action = "idle"
        self.tick = 0
        self.vx = 0.0
        self.vy = 0.0
        self.walk_dist = 0.0
        self.flying = False
        self.target_was_air = False
        self.celebrate = 0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Reações rápidas: latir, levar susto
        self.react = None
        self.react_timer = 0
        self.react_len = 0
        self.target_prev = "normal"
        self.fly_timer = 0
        self.scared = 0
        self.fetch = None
        self.busca = None        # buscando o ponteiro do mouse
        self.target_phase = None
        self.raio = 1.0          # tamanho pelo raio encolhedor (1 = normal)
        self.raio_alvo = 1.0
        self.sono_t = 0          # dormindo junto com o Jimmy
        self.acorda_t = 0

    def on_launch(self):
        self.running_fast = True

    def sleep_logic(self, t):
        """Dorme junto com o Jimmy: boceja, deita e dorme; quando ele acorda, se espreguiça."""
        v = vel()
        if t.sequence_state == "sleeping" and not self.fetch:
            if self.sono_t == 0 and abs(t.x - self.x) > 90 * v:
                return False   # ainda está indo para perto do Jimmy
            self.sono_t += 1
            k = self.sono_t
            if t.sleep_kind in ("cochilo_pe", "cochilo_sentado"):
                anim, i = "goddard_cochila_pe", 0
            elif k < 40:
                anim, i = "goddard_boceja", (k // 10) % 2
            elif k < 70:
                anim, i = "goddard_deita", min((k - 40) // 15, 1)
            else:
                anim, i = "goddard_dorme", (k - 70) // 20   # respirando com os "Zzz"
        elif self.sono_t > 0:
            self.acorda_t += 1
            k = self.acorda_t
            anim, i = ("goddard_espreguica", 0) if k < 22 else ("goddard_sono", 0)
            if k > 45:
                self.sono_t = self.acorda_t = 0
                return False
        else:
            return False
        self.vx = 0.0
        self.set_box(int(round(self.anim_box(anim) * self.raio)))
        self.set_image(self.frame(anim, i, "goddard_idle"), flip=(self.direction == -1))
        self.update_pos(self.x, self.ground_y)
        return True

    def start_busca(self):
        self.busca = {"fase": "espera", "t": 0}
        self.fetch = None
        self.react = None

    def boca(self):
        """Onde fica a boca do Goddard (coordenadas da tela, sem OX/OY)."""
        return (self.x + self.box * (0.84 if self.direction == 1 else 0.16), self.y + self.box * 0.44)

    def busca_logic(self, t):
        b, v = self.busca, vel()
        b["t"] += 1
        c = QCursor.pos()
        cx, cy = c.x() - OX, c.y() - OY
        if b["fase"] == "espera":
            # Ouve o Jimmy, late e liga o jetpack
            if b["t"] == 95: self.start_react("bark", 30)
            if b["t"] < 125:
                if self.react:
                    self.react_logic()
                else:
                    self.set_box(int(round(self.anim_box("goddard_idle") * self.raio)))
                    self.set_image(self.frame("goddard_idle", 0, "goddard_idle"), flip=(self.direction == -1))
                return
            b["fase"], b["cursor"] = "indo", (cx, cy)
            self.react = None
            self.flying, self.fly_timer = True, 0
            tocar("jetpack_liga")
        # Você mexeu no mouse: o Goddard desiste (a busca acaba)
        if b["fase"] == "indo" and math.hypot(cx - b["cursor"][0], cy - b["cursor"][1]) > 40:
            return self.fim_busca(False)
        if b["fase"] == "levando" and math.hypot(cx - b["solto"][0], cy - b["solto"][1]) > 25:
            return self.fim_busca(False)
        self.fly_timer += 1
        som_loop("jetpack", self.fly_timer > 8)
        if b["fase"] == "indo":
            self.direction = 1 if cx > self.x + self.box / 2 else -1
            gx = cx - self.box * (0.84 if self.direction == 1 else 0.16)
            gy = cy - self.box * 0.44
        else:
            # Leva até a mão do Jimmy, do lado de fora dele
            lado = 1 if self.x + self.box / 2 < t.x + t.box / 2 else -1
            gx = t.x + t.box / 2 - self.box / 2 - lado * 0.75 * t.box
            gy = t.y + t.box * 0.3
            self.direction = lado
        gy = min(gy, self.ground_y)
        lim = 7 * v
        if self.fly_timer < 18:
            self.vy += (-4 * v - self.vy) * 0.2
            self.vx *= 0.9
        else:
            self.vx += (max(-lim, min(lim, (gx - self.x) * 0.06)) - self.vx) * 0.15
            self.vy += (max(-lim, min(lim, (gy - self.y) * 0.06)) - self.vy) * 0.15
        self.x = max(0, min(self.x + self.vx, self.sw - self.box))
        self.y = max(0, min(self.y + self.vy + math.sin(self.tick * 0.15) * 0.6 * v, self.ground_y))
        speed = math.hypot(self.vx, self.vy) / v
        if self.fly_timer < 18:
            anim, i = "goddard_takeoff", self.fly_timer // 6
        elif speed > 2.5:
            anim, i = "goddard_fly", self.tick // 4
        else:
            anim, i = "goddard_hover", self.tick // 10
        self.update_depth()
        self.depth *= self.raio
        self.show_anim(anim, i, flip=(self.direction == -1), anchor="bottom" if self.fly_timer < 18 else "center",
                       fallback="goddard_run1")
        self.update_pos(self.x, self.y)
        if FX and self.tick % 3 == 0:
            FX.smoke(self.x + self.box * random.uniform(0.3, 0.6), self.y + self.box * 0.92, random.uniform(2.5, 4.5),
                     life=22, vx=-self.vx * 0.2, vy=1.2, gray=random.randint(215, 240), alpha=0.4, grow=1.5)
        mx, my = self.boca()
        perto = math.hypot(gx - self.x, gy - self.y) < 14 * v
        if b["fase"] == "indo" and self.fly_timer > 18 and perto:
            # Nhac! Mordeu o ponteiro
            b["fase"] = "levando"
            tocar("latido")
            stat("ponteiros")
        if b["fase"] == "levando":
            b["solto"] = (int(mx), int(my))
            QCursor.setPos(int(mx) + OX, int(my) + OY)
            if self.fly_timer > 18 and perto and abs(self.vx) < 1.5 * v:
                self.fim_busca(True)

    def fim_busca(self, entregou):
        self.busca = None
        self.fly_timer = 18          # o voo normal traz ele de volta ao chão
        if MANAGER: MANAGER.fim_busca_mouse(entregou)

    def encolher(self, sim):
        self.raio_alvo = 0.45 if sim else 1.0

    def fetch_logic(self, t, v):
        """Busca a bolinha: corre até ela, pega com a boca e leva até o Jimmy. Retorna o x alvo ou None."""
        b = BALL
        if b is None or not b.isVisible() or b.dragging:
            if self.fetch and b is not None and b.held_by is self: b.held_by = None
            self.fetch = None
            return None
        if self.fetch is None:
            if b.thrown and b.held_by is None:
                self.fetch = "chasing"
            else:
                return None
        if self.fetch == "chasing":
            if b.held_by is not None:
                self.fetch = None
                return None
            mouth = 0.86 if b.bx > self.x + self.box / 2 else 0.14
            goal = b.bx - self.box * mouth
            if abs(goal - self.x) < 10 * v and b.by > b.ground - 25 * v:
                b.held_by = self   # pegou!
                b.vx = b.vy = 0.0
                self.fetch = "returning"
            return goal
        # Levando de volta para o Jimmy
        side = 1 if self.x < t.x else -1
        goal = t.x + t.box / 2 - self.box / 2 - 70 * v * side
        if abs(goal - self.x) < 12 * v:
            b.held_by = None   # solta na frente do Jimmy
            b.vx, b.vy = side * 2 * v, -4 * v
            b.thrown = False
            stat("bolinhas")
            if CFG["goddard_pet"]: gd_add("diversao", 25)
            self.fetch = None
            self.celebrate = 1
            return None
        return goal

    def mousePressEvent(self, e):
        # Clicou no Goddard (no chão): late ou pula de alegria (e ganha um carinho)
        if e.button() != Qt.MouseButton.LeftButton or self.flying or self.react: return
        self.idle_timer = 0
        if CFG["goddard_pet"]: gd_add("diversao", 4)
        r = random.random()
        if r < 0.35:
            self.start_react("bark", 30)
        elif r < 0.7:
            self.start_react("jump", 26)
        else:
            self.start_react("truque")

    def enterEvent(self, e):
        self.mouse_em_cima = True

    def leaveEvent(self, e):
        self.mouse_em_cima = False

    def cuidar_logic(self):
        """Medidor quando o mouse está em cima; de vez em quando pede o que está faltando."""
        if not hasattr(self, "medidor"):
            self.medidor = MedidorGoddard()
            self.bubble_gd = Bubble(lambda: None)
            self.pedido_t = 0
            self.proximo_pedido = time.time() + 120
        if not CFG["goddard_pet"] or not self.isVisible():
            self.medidor.hide(); self.bubble_gd.hide()
            return
        if getattr(self, "mouse_em_cima", False):
            self.medidor.follow(self)
        else:
            self.medidor.hide()
        if self.pedido_t > 0:
            self.pedido_t -= 1
            self.bubble_gd.follow(self)
            if self.pedido_t == 0: self.bubble_gd.hide()
        elif time.time() >= self.proximo_pedido and not self.flying and not quieto():
            falta = [(gd_get(k), ico) for k, ico in GD_ITENS if gd_get(k) < 25]
            self.proximo_pedido = time.time() + 240
            if falta:
                self.bubble_gd.say(min(falta)[1] + "❓")
                self.pedido_t = 120
                if not self.react: self.start_react("pede")

    def cuidar(self, tipo):
        if tipo == "oleo":
            gd_add("oleo", 45)
            fala, anim = "Óleo! 😋", "comer"
        elif tipo == "banho":
            gd_add("limpeza", 60)
            fala, anim = "Que limpinho! ✨", "banho"
            if FX: FX.bolhas(self.x + self.box / 2, self.y + self.box * 0.6, 14)
        else:
            gd_add("diversao", 10)
            fala, anim = "Au au! 🎾", "brincar"
        stat("cuidados")
        tocar("goddard")
        if not self.flying:
            self.react = None
            self.start_react(anim, 26)
        if hasattr(self, "bubble_gd"):
            self.bubble_gd.say(fala)
            self.pedido_t = 70

    def pause(self):
        som_loop("jetpack", False)
        if hasattr(self, "medidor"):
            self.medidor.hide(); self.bubble_gd.hide()
        super().pause()

    def shutdown(self):
        som_loop("jetpack", False)
        if hasattr(self, "medidor"):
            self.medidor.close(); self.bubble_gd.close()
        super().shutdown()

    # Interações: (animação, quadro) em sequência, cada um por N ticks
    ROTEIROS = {
        "pede":    ([("goddard_pede", 0), ("goddard_pede", 1)] * 3, 12),
        "comer":   ([("goddard_pede", 0), ("goddard_come", 0)] + [("goddard_come", 1), ("goddard_come", 2)] * 4
                    + [("goddard_come", 3)] * 2, 11),
        "banho":   ([("goddard_banho", 0)] * 2 + [("goddard_banho", 1), ("goddard_banho", 2)] * 2
                    + [("goddard_banho", 3)] * 2 + [("goddard_banho", 4)] * 2, 14),
        "brincar": ([("goddard_brinca", 0), ("goddard_brinca", 1), ("goddard_brinca", 2), ("goddard_brinca", 3)] * 2, 10),
    }

    def start_react(self, kind, ticks=0):
        if kind == "truque":
            # Um truque sorteado: plantar bananeira, rolar, ficar em pé ou fazer charme
            self.roteiro = [("goddard_truque", random.randint(0, 3))] * 3
            self.roteiro_passo = 15
        elif kind in self.ROTEIROS:
            self.roteiro, self.roteiro_passo = self.ROTEIROS[kind]
        if kind in self.ROTEIROS or kind == "truque":
            if not self.has_anim(self.roteiro[0][0]):
                kind = "jump"   # folha nova não encontrada: usa o pulinho antigo
            else:
                ticks = len(self.roteiro) * self.roteiro_passo
        self.react, self.react_timer, self.react_len = kind, 0, ticks
        if kind == "bark": tocar("latido")
        if kind == "jump": tocar("goddard")

    def react_logic(self):
        """Para no lugar e faz a reação. Retorna True enquanto ela durar."""
        self.react_timer += 1
        self.vx *= 0.8
        self.x = max(0, min(self.x + self.vx, self.sw - self.box))
        hop = 0
        if self.react in self.ROTEIROS or self.react == "truque":
            k = min(len(self.roteiro) - 1, self.react_timer // self.roteiro_passo)
            anim, i = self.roteiro[k]
            img = self.frame(anim, i, "goddard_idle")
            if self.react == "brincar" and i == 1:
                hop = 12 * vel()   # pulo atrás da bolinha
            elif self.react == "banho" and i in (1, 2) and FX and self.react_timer % 6 == 0:
                FX.bolhas(self.x + self.box / 2, self.y + self.box * 0.55, 3)
            elif self.react == "comer" and i in (1, 2) and self.react_timer % 11 == 0:
                tocar("bolinha")   # nham
        elif self.react == "bark":
            # Boca abre junto com cada "au" do som (0-0,17 s e 0,34-0,54 s)
            k = self.react_timer
            aberta = k < 6 or 12 <= k < 19
            img = self.frame("goddard_bark", 1 if aberta else 0, "goddard_idle")
            hop = 3 * vel() if aberta else 0
        elif self.react == "jump":
            # Pulo de alegria quando clicam nele
            phase = self.react_timer / self.react_len
            hop = math.sin(phase * math.pi) * 30 * vel()
            img = self.frame("goddard_jump", 0 if phase < 0.5 else 1, "goddard_idle")
        else:
            # Susto: cabeça infla e dá um pulinho para trás
            img = self.frame("goddard_surprise", 0, "goddard_idle")
            if self.react_timer < 8:
                hop = math.sin(self.react_timer / 8 * math.pi) * 14 * vel()
                self.x = max(0, min(self.x - self.direction * 1.5 * vel(), self.sw - self.box))
        self.set_image(img, flip=(self.direction == -1))
        self.update_pos(self.x, self.ground_y - hop)
        if self.react_timer >= self.react_len:
            self.react = None
        return True

    def follow_logic(self):
        try:
            self.tick += 1
            self.cuidar_logic()
            t = self.target
            # Jimmy acabou de pousar: Goddard vai comemorar quando chegar perto
            if self.target_was_air and not t.in_air:
                self.celebrate = 1
            self.target_was_air = t.in_air
            # Late quando o foguete liga o motor; leva susto quando ele explode
            if t.sequence_state != self.target_prev:
                if not self.flying:
                    if t.sequence_state == "ignition":
                        self.start_react("bark", 30)
                    elif t.sequence_state == "exploding":
                        self.start_react("surprise", 45)
                elif t.sequence_state == "exploding":
                    self.scared = 45  # susto no ar
                if t.sequence_state == "party" and not self.flying:
                    self.celebrate = 1  # comemora junto
                if t.sequence_state == "visit" and not self.flying and not self.react:
                    self.start_react("bark", 30)  # festa para o amigo que chegou
                self.target_prev = t.sequence_state
            # Susto com o BRAIN BLAST
            if t.phase != self.target_phase:
                if t.phase == "blast" and not self.flying and not self.react:
                    self.start_react("surprise", 45)
                self.target_phase = t.phase
            if self.busca:
                self.busca_logic(t)
                return
            if self.react and not self.flying and self.react_logic():
                return
            # Jetpack só se existir animação de voo (goddard_fly); senão corre pelo chão.
            # Decola quando o foguete sobe (na ignição ele fica latindo)
            if t.in_air and t.sequence_state != "ignition" and self.has_anim("goddard_fly") and not self.flying:
                self.flying = True
                self.fly_timer = 0
                self.react = None
                tocar("jetpack_liga")
            # Chiado do jetpack enquanto voa (a partir do fim do "fwoosh" da ignição)
            som_loop("jetpack", self.flying and self.fly_timer > 8)

            if self.flying:
                self.fly_timer += 1
                v = vel()
                # Vai atrás do Jimmy pelo ar, um pouco abaixo e ao lado dele
                if t.in_air:
                    side = 1 if t.x > self.x else -1
                    goal_x = t.x + t.box / 2 - self.box / 2 - 110 * v * side
                    goal_y = min(t.y + t.box * 0.6, self.ground_y)
                else:
                    goal_x, goal_y = self.x, self.ground_y
                lim = 9 * v
                taking_off = self.fly_timer < 18
                if taking_off:
                    # Decolagem: sobe quase reto com a chama azul
                    self.vy += (-4 * v - self.vy) * 0.2
                    self.vx *= 0.9
                else:
                    self.vx += (max(-lim, min(lim, (goal_x - self.x) * 0.05)) - self.vx) * 0.1
                    self.vy += (max(-lim, min(lim, (goal_y - self.y) * 0.05)) - self.vy) * 0.1
                self.x = max(0, min(self.x + self.vx, self.sw - self.box))
                self.y = min(self.y + self.vy + math.sin(self.tick * 0.15) * 0.8 * v, self.ground_y)
                if abs(self.vx) > 0.3 * v: self.direction = 1 if self.vx > 0 else -1
                speed = math.hypot(self.vx, self.vy) / v
                angle = 0
                if taking_off:
                    anim, i = "goddard_takeoff", self.fly_timer // 6
                elif self.scared > 0:
                    self.scared -= 1
                    anim, i = "goddard_hover_scared", self.tick // 4
                elif speed > 6:
                    anim, i, angle = "goddard_fly_fast", self.tick // 3, self.vy * 1.5 * self.direction
                elif speed > 2.5:
                    anim, i, angle = "goddard_fly", self.tick // 4, self.vy * 2 * self.direction
                else:
                    anim, i = "goddard_hover", self.tick // 10
                self.update_depth()
                self.depth *= self.raio
                self.show_anim(anim, i, flip=(self.direction == -1), angle=angle,
                               anchor="bottom" if taking_off else "center", fallback="goddard_run1")
                # Fumacinha das patas
                if FX and self.tick % 3 == 0:
                    FX.smoke(self.x + self.box * random.uniform(0.3, 0.6), self.y + self.box * 0.92,
                             random.uniform(2.5, 4.5), life=22, vx=-self.vx * 0.2, vy=1.2,
                             gray=random.randint(215, 240), alpha=0.4, grow=1.5)
                # Jimmy pousou e Goddard chegou no chão: desliga o jetpack
                if not t.in_air and self.y >= self.ground_y - 1:
                    self.flying = False
                    self.running_fast = False
                    self.show_anim("goddard_idle", 0, flip=(self.direction == -1), fallback="goddard_idle")
                    self.y = self.ground_y
                self.update_pos(self.x, self.y)
                return

            # Tamanho da janela do Goddard no chão (o voo usa outro)
            self.depth = 1.0
            self.raio += (self.raio_alvo - self.raio) * 0.15   # encolhe/cresce aos poucos
            if abs(self.raio - self.raio_alvo) < 0.01: self.raio = self.raio_alvo
            # Primeiro decide o que ele está fazendo; a janela muda de tamanho uma vez só
            # (antes ia para o tamanho "em pé" e voltava a cada quadro, e o Goddard piscava)
            if self.sleep_logic(t):
                return
            if t.sequence_state == "danca" and not self.fetch and abs(t.x - self.x) < 160 * vel():
                # Dança do lado do Jimmy
                self.vx = 0.0
                self.set_box(int(round(self.anim_box("goddard_danca") * self.raio)))
                self.set_image(self.frame("goddard_danca", self.tick // 9, "goddard_idle"), flip=(self.direction == -1))
                self.update_pos(self.x, self.ground_y)
                return
            self.set_box(int(round(self.anim_box("goddard_idle") * self.raio)))
            # No chão: segue o Jimmy (ou a bolinha) guardando uma distância, acelerando e freando suave
            v = vel()
            goal = self.fetch_logic(t, v)
            if goal is not None:
                dx = goal - self.x
                keep = 4 * v
            else:
                dx = t.x - self.x
                keep = (80 if not t.in_air else 20) * v
            target_speed = 0.0
            if abs(dx) > keep:
                fast = goal is not None or self.running_fast or t.in_air or abs(dx) > 400 * v
                target_speed = 7 * v if fast else min(3.5 * v, abs(dx) / 40)
                if goal is not None:
                    target_speed = min(target_speed, max(1.5 * v, abs(dx) / 6))  # freia chegando na bolinha
                self.direction = 1 if dx > 0 else -1
            self.vx += (self.direction * target_speed - self.vx) * 0.1
            self.x = max(0, min(self.x + self.vx, self.sw - self.box))
            self.walk_dist += abs(self.vx)
            speed = abs(self.vx)
            flip = self.direction == -1
            hop = 0
            if speed > 4.5 * v:
                self.idle_timer = 0
                # Correndo até o Jimmy depois do pouso: língua de fora
                run = "goddard_run_happy" if (self.celebrate or self.fetch) else "goddard_run"
                img = self.frame(run, int(self.walk_dist / (18 * v)), "goddard_run1")
            elif speed > 0.35 * v:
                self.idle_timer = 0
                img = self.frame("goddard_walk", int(self.walk_dist / (10 * v)), "goddard_walk1")
            elif self.celebrate:
                # Chegou perto do Jimmy depois do pouso: pula de alegria e fica ofegante
                if self.celebrate == 1: tocar("goddard")
                self.celebrate += 1
                self.running_fast = False
                if self.celebrate < 70:
                    phase = (self.celebrate % 23) / 23
                    hop = math.sin(phase * math.pi) * 28 * v
                    img = self.frame("goddard_jump", 0 if phase < 0.5 else 1, "goddard_idle")
                elif self.celebrate < 150:
                    img = self.frame("goddard_happy", self.celebrate // 6, "goddard_idle")
                else:
                    self.celebrate = 0
                    img = self.frame("goddard_idle", 0, "goddard_idle")
            else:
                self.idle_timer += 1
                self.running_fast = False
                # Parado: de tempos em tempos escolhe outra coisa para fazer
                if self.idle_timer % 150 == 0 and t.sequence_state == "sleeping":
                    self.idle_action = "sit"  # fica sentado quietinho do lado do Jimmy dormindo
                elif self.idle_timer % 150 == 0:
                    self.idle_action = random.choice(["idle", "sit", "sit", "sniff", "happy", "bark"])
                    if self.idle_action == "bark":
                        self.idle_action = "idle"
                        self.start_react("bark", 30)
                if self.idle_timer < 60 or self.idle_action == "idle":
                    img = self.frame("goddard_idle", 0, "goddard_idle")
                elif self.idle_action == "sit":
                    # Sentado; de vez em quando se mexe
                    i = (self.idle_timer // 7) % 3 if (self.idle_timer // 50) % 3 == 1 else 0
                    img = self.frame("goddard_sit", i, "goddard_sit")
                elif self.idle_action == "sniff":
                    img = self.frame("goddard_sniff", 0, "goddard_idle")
                    self.x += 0.3 * v * self.direction * (1 if (self.idle_timer // 20) % 2 else 0)
                else:
                    img = self.frame("goddard_happy", self.idle_timer // 6, "goddard_idle")
            if speed <= 0.35 * v and not self.celebrate and not self.fetch:
                flip = self.look_at_mouse(flip)   # parado: vira para o lado do mouse
            self.set_image(img, flip=flip)
            self.update_pos(self.x, self.ground_y - hop)
        except Exception as e: log_error(e)

class Configuracoes(QWidget):
    """Janela aberta pelo ícone da bandeja. Tudo é salvo e aplicado na hora."""
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Configurações - Jimmy Neutron Pet")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(400)

        self.tamanho = QSlider(Qt.Orientation.Horizontal)
        self.tamanho.setRange(10, 100)
        self.tamanho.setSingleStep(5)
        self.tamanho.setPageStep(10)
        self.tamanho_lbl = QLabel()
        self.tamanho_lbl.setMinimumWidth(40)
        linha = QHBoxLayout()
        linha.addWidget(self.tamanho)
        linha.addWidget(self.tamanho_lbl)
        self.tamanho_gd = QSlider(Qt.Orientation.Horizontal)
        self.tamanho_gd.setRange(50, 150)
        self.tamanho_gd.setSingleStep(5)
        self.tamanho_gd.setPageStep(10)
        self.tamanho_gd_lbl = QLabel()
        self.tamanho_gd_lbl.setMinimumWidth(40)
        linha_gd = QHBoxLayout()
        linha_gd.addWidget(self.tamanho_gd)
        linha_gd.addWidget(self.tamanho_gd_lbl)

        self.viagem_min = QSpinBox(); self.viagem_min.setRange(1, 120); self.viagem_min.setSuffix(" min")
        self.viagem_max = QSpinBox(); self.viagem_max.setRange(1, 120); self.viagem_max.setSuffix(" min")
        self.goddard = QCheckBox("Mostrar o Goddard")
        self.botao = QCheckBox("Mostrar o botão 🚀 LANÇAR")
        self.foguete_aleatorio = QCheckBox("Foguete aparece em lugar aleatório")
        self.autostart = QCheckBox("Iniciar junto com o Windows")
        self.tela_cheia = QCheckBox("Esconder em jogos/vídeos em tela cheia")
        self.dormir = QCheckBox("Dormir à noite (22h às 6h) e cochilar")

        form = QFormLayout()
        form.addRow("Tamanho:", linha)
        form.addRow("🐶 Goddard:", linha_gd)
        self.vel_foguete = QComboBox()
        for key, nome, _ in VEL_FOGUETE:
            self.vel_foguete.addItem(nome, key)
        form.addRow("Foguete:", self.vel_foguete)
        # Intervalo das viagens numa linha só: "1 min até 5 min"
        linha_viagem = QHBoxLayout()
        linha_viagem.addWidget(self.viagem_min)
        linha_viagem.addWidget(QLabel("até"))
        linha_viagem.addWidget(self.viagem_max)
        form.addRow("Viagens:", linha_viagem)
        form.addRow(self.goddard)
        form.addRow(self.botao)
        form.addRow(self.foguete_aleatorio)
        form.addRow(self.autostart)
        form.addRow(self.tela_cheia)
        form.addRow(self.dormir)
        self.monitor = QComboBox()
        self.monitor.addItem("Principal", -1)
        if len(QApplication.screens()) > 1:
            self.monitor.addItem("Todos (atravessar)", -2)
        for i, scr in enumerate(QApplication.screens()):
            g = scr.geometry()
            self.monitor.addItem(f"Monitor {i + 1} ({g.width()}x{g.height()})", i)
        form.addRow("Monitor:", self.monitor)
        self.idioma = QComboBox()
        self.idioma.addItem("Português", "pt")
        self.idioma.addItem("English", "en")
        form.addRow("Idioma:", self.idioma)

        self.sons = QCheckBox("Ativar sons")
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setPageStep(10)
        self.volume_lbl = QLabel()
        self.volume_lbl.setMinimumWidth(40)
        linha_vol = QHBoxLayout()
        linha_vol.addWidget(self.volume)
        linha_vol.addWidget(self.volume_lbl)
        self.saida = QComboBox()
        testar = QPushButton("▶ Testar")
        testar.clicked.connect(lambda: SONS and SONS.tocar("explosao", forcar=True))
        form_som = QFormLayout()
        form_som.addRow(self.sons)
        self.som_jimmy = QCheckBox("Jimmy (paraquedas, pouso)")
        self.som_ronco = QCheckBox("Ronco (Jimmy dormindo)")
        self.som_goddard = QCheckBox("Goddard (latido, bip, jetpack)")
        self.som_foguete = QCheckBox("Foguete (decolagem, explosão)")
        for w in (self.som_jimmy, self.som_ronco, self.som_goddard, self.som_foguete):
            form_som.addRow(w)
        form_som.addRow("Volume:", linha_vol)
        form_som.addRow("Saída:", self.saida)
        form_som.addRow("", testar)

        padrao = QPushButton("Restaurar padrão")
        fechar = QPushButton("Fechar")
        padrao.clicked.connect(self.restaurar)
        fechar.clicked.connect(self.close)
        botoes = QHBoxLayout()
        botoes.addWidget(padrao)
        botoes.addStretch()
        botoes.addWidget(fechar)

        layout = QVBoxLayout(self)

        # Lembretes: liga/desliga + intervalo de cada um
        form_av = QFormLayout()
        self.avisos_on = QCheckBox("Ativar lembretes")
        self.som_avisos = QCheckBox("Tocar som nos avisos")
        form_av.addRow(self.avisos_on)
        form_av.addRow(self.som_avisos)
        self.avisos = {}
        for kind, rotulo in (("agua", "💧 Água"), ("pausa", "😌 Pausa"),
                             ("comer", "🍎 Comer"), ("exercicio", "💪 Exercício")):
            chk = QCheckBox(rotulo)
            spin = QSpinBox(); spin.setRange(5, 600); spin.setSingleStep(5); spin.setPrefix("a cada "); spin.setSuffix(" min")
            linha_av = QHBoxLayout(); linha_av.addWidget(chk); linha_av.addStretch(); linha_av.addWidget(spin)
            form_av.addRow(linha_av)
            self.avisos[kind] = (chk, spin)
        self.aviso_dormir = QCheckBox("💤 Hora de dormir (22h)")
        form_av.addRow(self.aviso_dormir)
        self.pomo_foco = QSpinBox(); self.pomo_foco.setRange(5, 120); self.pomo_foco.setSuffix(" min")
        self.pomo_pausa = QSpinBox(); self.pomo_pausa.setRange(1, 60); self.pomo_pausa.setSuffix(" min")
        linha_pomo = QHBoxLayout()
        linha_pomo.addWidget(QLabel("🍅 Pomodoro: foco"))
        linha_pomo.addWidget(self.pomo_foco)
        linha_pomo.addWidget(QLabel("pausa"))
        linha_pomo.addWidget(self.pomo_pausa)
        form_av.addRow(linha_pomo)
        self.bateria = QCheckBox("🔋 Avisar bateria fraca (notebook)")
        form_av.addRow(self.bateria)
        testar_aviso = QPushButton("▶ Testar aviso")
        testar_aviso.clicked.connect(self.testar_aviso)
        form_av.addRow("", testar_aviso)

        # Extras: Brain Blast, ausência, datas comemorativas
        form_ex = QFormLayout()
        self.ideias = QCheckBox("⚡ Brain Blast de vez em quando")
        self.ausente = QCheckBox("😴 Cochilar quando eu sair do PC")
        self.ausente_min = QSpinBox(); self.ausente_min.setRange(1, 120)
        self.ausente_min.setPrefix("após "); self.ausente_min.setSuffix(" min")
        linha_aus = QHBoxLayout(); linha_aus.addWidget(self.ausente); linha_aus.addStretch(); linha_aus.addWidget(self.ausente_min)
        self.datas = QCheckBox("🎉 Comemorar datas especiais")
        self.aniv_dia = QSpinBox(); self.aniv_dia.setRange(0, 31); self.aniv_dia.setSpecialValueText("dia")
        self.aniv_mes = QSpinBox(); self.aniv_mes.setRange(0, 12); self.aniv_mes.setSpecialValueText("mês")
        linha_aniv = QHBoxLayout()
        linha_aniv.addWidget(QLabel("🎂 Meu aniversário:"))
        linha_aniv.addWidget(self.aniv_dia); linha_aniv.addWidget(QLabel("/")); linha_aniv.addWidget(self.aniv_mes)
        linha_aniv.addStretch()
        self.amigos = QCheckBox("👫 Visitas dos amigos (Carl, Sheen, Libby, Cindy)")
        b_blast = QPushButton("⚡ Brain Blast")
        b_festa = QPushButton("🎉 Festa")
        b_amigo = QPushButton("👫 Amigo")
        b_blast.clicked.connect(self.testar_blast)
        b_festa.clicked.connect(self.testar_festa)
        b_amigo.clicked.connect(lambda: self.manager.spawn_friend())
        linha_bt = QHBoxLayout(); linha_bt.addWidget(QLabel("Testar:"))
        linha_bt.addWidget(b_blast); linha_bt.addWidget(b_festa); linha_bt.addWidget(b_amigo)
        form_ex.addRow(self.ideias)
        form_ex.addRow(linha_aus)
        form_ex.addRow(self.datas)
        form_ex.addRow(linha_aniv)
        form_ex.addRow(self.amigos)
        self.frases = QCheckBox("💬 Frases ao passar o mouse no Jimmy")
        form_ex.addRow(self.frases)
        self.tom_noite = QCheckBox("🌙 Tom de noite (escurece à noite)")
        form_ex.addRow(self.tom_noite)
        b_exp = QPushButton("💾 Exportar...")
        b_imp = QPushButton("📂 Importar...")
        b_exp.clicked.connect(self.exportar)
        b_imp.clicked.connect(self.importar)
        linha_io = QHBoxLayout(); linha_io.addWidget(QLabel("Configurações:"))
        linha_io.addWidget(b_exp); linha_io.addWidget(b_imp)
        form_ex.addRow(linha_io)
        form_ex.addRow(linha_bt)
        self.invencoes = QCheckBox("🧪 Invenções do Jimmy")
        self.lhamas = QCheckBox("🦙 Lhamas do Carl")
        self.passeios = QCheckBox("🛸 Passeios")
        linha_il = QHBoxLayout(); linha_il.addWidget(self.invencoes); linha_il.addWidget(self.lhamas); linha_il.addWidget(self.passeios)
        form_ex.addRow(linha_il)
        self.dancar = QCheckBox("💃 Dançar quando tocar música")
        self.curiosidades = QCheckBox("🔬 Curiosidades de ciência")
        b_cur = QPushButton("🔬 Testar")
        b_cur.clicked.connect(lambda: self.manager.queue.append(
            ("curiosidade", "🔬 " + random.choice(CURIOSIDADES), "ideia_ideia", True)))
        linha_dc = QHBoxLayout(); linha_dc.addWidget(self.dancar); linha_dc.addWidget(self.curiosidades); linha_dc.addWidget(b_cur)
        form_ex.addRow(linha_dc)
        self.easter = QCheckBox("🔤 Digitar \"neutron\" faz um Brain Blast (lê o teclado)")
        form_ex.addRow(self.easter)
        b_inv = QPushButton("🧪 Invenção")
        b_lha = QPushButton("🦙 Lhamas")
        b_inv.clicked.connect(lambda: self.manager.jimmy and self.manager.jimmy.sequence_state == "normal"
                              and self.manager.jimmy.start_invencao())
        b_lha.clicked.connect(lambda: self.manager.solta_lhamas())
        b_pas = QPushButton("🛸 Passeio")
        b_pas.clicked.connect(lambda: self.manager.jimmy and self.manager.jimmy.go_to_rocket(passeio=True))
        linha_bt2 = QHBoxLayout(); linha_bt2.addWidget(QLabel("Testar:")); linha_bt2.addWidget(b_inv); linha_bt2.addWidget(b_lha)
        linha_bt2.addWidget(b_pas)
        self.goddard_pet = QCheckBox("🐶 Cuidar do Goddard")
        self.meteoros = QCheckBox("☄️ Meteoros")
        b_met = QPushButton("☄️ Testar")
        b_met.clicked.connect(lambda: self.manager.start_meteoros())
        self.busca_mouse = QCheckBox("🖱️ Buscar o ponteiro")
        self.consertos = QCheckBox("🔧 Consertos")
        self.resgate_lhama = QCheckBox("🪐 Resgate da lhama")
        linha_gm = QHBoxLayout(); linha_gm.addWidget(self.goddard_pet); linha_gm.addWidget(self.meteoros); linha_gm.addWidget(b_met)
        linha_gm.addWidget(self.busca_mouse)
        linha_gm.addWidget(self.consertos)
        linha_gm.addWidget(self.resgate_lhama)
        form_ex.addRow(linha_bt2)
        form_ex.addRow(linha_gm)
        self._festa_i = 0

        # Abas: Geral / Sons / Lembretes / Extras
        # Clima
        form_cl = QFormLayout()
        self.clima_on = QCheckBox("🌦️ Avisar o clima de manhã")
        self.cidade = QLineEdit(); self.cidade.setPlaceholderText("ex.: São Paulo")
        buscar = QPushButton("Buscar")
        buscar.clicked.connect(self.buscar_clima)
        self.cidade.returnPressed.connect(self.buscar_clima)
        linha_cid = QHBoxLayout(); linha_cid.addWidget(self.cidade); linha_cid.addWidget(buscar)
        self.clima_status = TLabel("")
        self.clima_status.setWordWrap(True)
        self.chuva = QCheckBox("☔ Mostrar chuva na tela quando estiver chovendo")
        nota = QLabel("Usa o Open-Meteo (gratuito, sem conta). Só o nome da cidade é enviado.")
        nota.setWordWrap(True)
        nota.setStyleSheet("color: gray; font-size: 10px;")
        form_cl.addRow(self.clima_on)
        form_cl.addRow("Cidade:", linha_cid)
        form_cl.addRow(self.clima_status)
        form_cl.addRow(self.chuva)
        b_chuva = QPushButton("☔ Testar chuva")
        b_chuva.clicked.connect(lambda: self.manager.start_rain())
        form_cl.addRow(b_chuva)
        self.estacoes = QCheckBox("🍂 Efeitos das estações (folhas, pétalas, neve)")
        b_est = QPushButton("🍂 Testar estação")
        b_est.clicked.connect(self.testar_estacao)
        linha_est = QHBoxLayout(); linha_est.addWidget(self.estacoes); linha_est.addWidget(b_est)
        form_cl.addRow(linha_est)
        self._est_i = 0
        form_cl.addRow(nota)

        # Conquistas
        form_cq = QFormLayout()
        self.cq_resumo = TLabel()
        self.cq_lista = TList()
        form_cq.addRow(self.cq_resumo)
        form_cq.addRow(self.cq_lista)

        # Meus lembretes
        form_ml = QFormLayout()
        self.ml_lista = TList()
        self.ml_lista.setMaximumHeight(120)
        self.ml_texto = QLineEdit(); self.ml_texto.setPlaceholderText("ex.: Reunião com a equipe")
        self.ml_hora = QTimeEdit(); self.ml_hora.setDisplayFormat("HH:mm")
        self.ml_rep = QComboBox()
        for key, nome in REPETICOES:
            self.ml_rep.addItem(nome, key)
        b_add = QPushButton("➕ Adicionar")
        b_del = QPushButton("🗑️ Remover")
        b_add.clicked.connect(self.add_meu)
        b_del.clicked.connect(self.del_meu)
        linha_ml = QHBoxLayout(); linha_ml.addWidget(self.ml_hora); linha_ml.addWidget(self.ml_rep)
        linha_mb = QHBoxLayout(); linha_mb.addWidget(b_add); linha_mb.addWidget(b_del)
        form_ml.addRow(self.ml_lista)
        form_ml.addRow("Lembrete:", self.ml_texto)
        form_ml.addRow("Quando:", linha_ml)
        form_ml.addRow(linha_mb)
        self.notas_lista = TList(); self.notas_lista.setMaximumHeight(100)
        b_nota_del = QPushButton("🗑️ Apagar nota")
        b_nota_del.clicked.connect(self.del_nota)
        form_ml.addRow(QLabel("🗒️ Notas rápidas (clique no Jimmy → Nota rápida):"))
        form_ml.addRow(self.notas_lista)
        form_ml.addRow(b_nota_del)

        # Apps: frases quando você abre certos programas
        form_ap = QFormLayout()
        self.apps_on = QCheckBox("🎮 Comentar quando eu abrir estes programas")
        self.ap_lista = TList(); self.ap_lista.setMaximumHeight(110)
        self.ap_exe = QLineEdit(); self.ap_exe.setPlaceholderText("ex.: spotify.exe")
        self.ap_frase = QLineEdit(); self.ap_frase.setPlaceholderText("ex.: Solta o som! 🎵")
        b_ap_add = QPushButton("➕ Adicionar"); b_ap_del = QPushButton("🗑️ Remover")
        b_ap_add.clicked.connect(self.add_app); b_ap_del.clicked.connect(self.del_app)
        linha_ap = QHBoxLayout(); linha_ap.addWidget(b_ap_add); linha_ap.addWidget(b_ap_del)
        self.app_ultimo = TLabel("Último programa usado: -")
        self.app_ultimo.setStyleSheet("color: gray; font-size: 10px;")
        form_ap.addRow(self.apps_on)
        form_ap.addRow(self.ap_lista)
        form_ap.addRow("Programa:", self.ap_exe)
        form_ap.addRow("Frase:", self.ap_frase)
        form_ap.addRow(linha_ap)
        form_ap.addRow(self.app_ultimo)

        # Online: rede local e atualização
        form_on = QFormLayout()
        self.rede_on = QCheckBox("📡 Visitar outros PCs da rede com o pet")
        self.rede_status = TLabel("")
        b_visitar = QPushButton("📡 Visitar agora")
        b_visitar.clicked.connect(lambda: self.manager.visitar_agora())
        nota_rede = QLabel("Na primeira vez o Windows pede para liberar no Firewall (rede privada).")
        nota_rede.setWordWrap(True); nota_rede.setStyleSheet("color: gray; font-size: 10px;")
        self.repo = QLineEdit(); self.repo.setPlaceholderText("usuario/repositorio")
        self.repo.editingFinished.connect(self.salvar_repo)
        self.atualizar_on = QCheckBox("🔎 Verificar atualizações automaticamente")
        self.atualizar_auto = QCheckBox("⬇️ Atualizar sozinho quando sair versão nova")
        b_proc = QPushButton("🔎 Procurar agora")
        b_proc.clicked.connect(lambda: (self.salvar_repo(), self.manager.check_update(manual=True)))
        b_upd = QPushButton("⬇️ Atualizar")
        b_upd.clicked.connect(lambda: self.manager.do_update())
        self.upd_status = TLabel("")
        self.upd_status.setWordWrap(True)
        linha_upd = QHBoxLayout(); linha_upd.addWidget(b_proc); linha_upd.addWidget(b_upd)
        form_on.addRow(self.rede_on)
        linha_rd = QHBoxLayout(); linha_rd.addWidget(self.rede_status); linha_rd.addStretch(); linha_rd.addWidget(b_visitar)
        form_on.addRow(linha_rd)
        form_on.addRow(nota_rede)
        self.divulgar = QCheckBox("📺 O Jimmy lembra do canal @oevetech (1 vez a cada 12–36 h)")
        form_on.addRow(self.divulgar)
        form_on.addRow(QLabel(f"Versão instalada: v{APP_VERSAO}"))
        form_on.addRow("GitHub:", self.repo)
        form_on.addRow(self.atualizar_on)
        form_on.addRow(self.atualizar_auto)
        form_on.addRow(linha_upd)
        form_on.addRow(self.upd_status)

        # Datas: contagem regressiva
        form_dt = QFormLayout()
        self.ct_lista = TList(); self.ct_lista.setMaximumHeight(130)
        self.ct_nome = QLineEdit(); self.ct_nome.setPlaceholderText("ex.: Viagem de férias")
        self.ct_data = QDateEdit(); self.ct_data.setCalendarPopup(True); self.ct_data.setDisplayFormat("dd/MM/yyyy")
        self.ct_data.setDate(QDate.currentDate().addDays(7))
        b_ct_add = QPushButton("➕ Adicionar"); b_ct_del = QPushButton("🗑️ Remover")
        b_ct_add.clicked.connect(self.add_contagem); b_ct_del.clicked.connect(self.del_contagem)
        linha_ct = QHBoxLayout(); linha_ct.addWidget(b_ct_add); linha_ct.addWidget(b_ct_del)
        form_dt.addRow(QLabel("⏳ O Jimmy avisa quantos dias faltam e comemora no dia."))
        form_dt.addRow(self.ct_lista)
        form_dt.addRow("Evento:", self.ct_nome)
        form_dt.addRow("Data:", self.ct_data)
        form_dt.addRow(linha_ct)

        abas = QTabWidget()
        abas.setUsesScrollButtons(True)
        for titulo, conteudo in (("Geral", form), ("Sons", form_som), ("Avisos", form_av), ("📝 Meus", form_ml),
                                 ("⏳ Datas", form_dt), ("Extras", form_ex), ("Apps", form_ap), ("Clima", form_cl),
                                 ("Online", form_on), ("🏆", form_cq)):
            pagina = QWidget()
            conteudo.setVerticalSpacing(6)
            pagina.setLayout(conteudo)
            abas.addTab(pagina, titulo)
        layout.addWidget(abas)
        layout.addLayout(botoes)

        # Rodapé: canal do desenvolvedor
        yt = QPixmap(22, 16)
        yt.fill(Qt.GlobalColor.transparent)
        pyt = QPainter(yt)
        pyt.setRenderHint(QPainter.RenderHint.Antialiasing)
        pyt.setPen(Qt.PenStyle.NoPen)
        pyt.setBrush(QColor(255, 0, 0))
        pyt.drawRoundedRect(0, 0, 22, 16, 4, 4)
        pyt.setBrush(QColor(255, 255, 255))
        pyt.drawPolygon(QPolygon([QPoint(9, 4), QPoint(9, 12), QPoint(15, 8)]))
        pyt.end()
        icone_yt = QLabel()
        icone_yt.setPixmap(yt)
        canal = QLabel('<a href="https://www.youtube.com/@oevetech" style="color:#cc0000; text-decoration:none;">'
                       '<b>@oevetech</b></a>')
        canal.setOpenExternalLinks(True)
        canal.setCursor(Qt.CursorShape.PointingHandCursor)
        canal.setToolTip("Abrir o canal no YouTube")
        rodape = QHBoxLayout()
        rodape.addStretch()
        rodape.addWidget(QLabel("Desenvolvedor:"))
        rodape.addWidget(icone_yt)
        rodape.addWidget(canal)
        rodape.addStretch()
        layout.addLayout(rodape)
        layout.setContentsMargins(8, 8, 8, 6)

        # O tamanho só é aplicado quando o slider para de mexer (recriar os pets a cada passo pisca)
        self.aplicar_tamanho = QTimer(self)
        self.aplicar_tamanho.setSingleShot(True)
        self.aplicar_tamanho.timeout.connect(self.salvar_tamanho)

        traduzir_janela(self)
        self.carregar()
        self.tamanho.valueChanged.connect(self.mudou_tamanho)
        self.tamanho_gd.valueChanged.connect(self.mudou_tamanho)
        self.viagem_min.valueChanged.connect(self.salvar_viagem)
        self.viagem_max.valueChanged.connect(self.salvar_viagem)
        self.goddard.toggled.connect(self.salvar_goddard)
        self.botao.toggled.connect(self.salvar_botao)
        self.sons.toggled.connect(self.salvar_sons)
        self.autostart.toggled.connect(set_autostart)
        self.tela_cheia.toggled.connect(self.salvar_tela_cheia)
        self.dormir.toggled.connect(self.salvar_dormir)
        self.vel_foguete.currentIndexChanged.connect(self.salvar_extras)
        for w in (self.som_jimmy, self.som_ronco, self.som_goddard, self.som_foguete, self.aviso_dormir,
                  self.avisos_on, self.som_avisos):
            w.toggled.connect(self.salvar_extras)
        for chk, spin in self.avisos.values():
            chk.toggled.connect(self.salvar_extras)
            spin.valueChanged.connect(self.salvar_extras)
        self.monitor.currentIndexChanged.connect(self.salvar_monitor)
        self.idioma.currentIndexChanged.connect(self.salvar_idioma)
        for w in (self.pomo_foco, self.pomo_pausa):
            w.valueChanged.connect(self.salvar_extras)
        for w in (self.ideias, self.ausente, self.datas, self.foguete_aleatorio, self.amigos, self.invencoes, self.lhamas, self.dancar, self.curiosidades, self.passeios, self.goddard_pet, self.meteoros, self.busca_mouse, self.divulgar, self.consertos, self.resgate_lhama,
                  self.estacoes, self.easter, self.apps_on, self.rede_on, self.atualizar_on, self.atualizar_auto,
                  self.bateria, self.frases, self.clima_on, self.chuva, self.tom_noite):
            w.toggled.connect(self.salvar_extras)
        for w in (self.ausente_min, self.aniv_dia, self.aniv_mes):
            w.valueChanged.connect(self.salvar_extras)
        self.volume.valueChanged.connect(self.salvar_sons)
        self.saida.currentIndexChanged.connect(self.salvar_sons)

    def carregar(self):
        widgets = (self.tamanho, self.tamanho_gd, self.viagem_min, self.viagem_max, self.goddard, self.botao,
                   self.sons, self.volume, self.saida, self.autostart, self.tela_cheia, self.dormir,
                   self.vel_foguete, self.som_jimmy, self.som_ronco, self.som_goddard, self.som_foguete, self.aviso_dormir,
                   self.avisos_on, self.som_avisos, self.ideias, self.ausente, self.ausente_min, self.foguete_aleatorio,
                   self.datas, self.aniv_dia, self.aniv_mes, self.amigos,
                   self.invencoes, self.lhamas, self.dancar, self.curiosidades, self.estacoes, self.idioma, self.passeios, self.goddard_pet, self.meteoros, self.busca_mouse, self.divulgar, self.consertos, self.resgate_lhama, self.easter, self.apps_on,
                   self.rede_on, self.atualizar_on, self.atualizar_auto,
                   self.monitor, self.pomo_foco, self.pomo_pausa, self.bateria, self.frases, self.clima_on, self.chuva,
                   self.tom_noite,
                   *[w for par in self.avisos.values() for w in par])
        for w in widgets: w.blockSignals(True)
        self.tamanho.setValue(int(CFG["tamanho"]))
        self.tamanho_gd.setValue(int(CFG["tamanho_goddard"]))
        self.tamanho_lbl.setText(f"{self.tamanho.value()}%")
        self.tamanho_gd_lbl.setText(f"{self.tamanho_gd.value()}%")
        self.tamanho_lbl.setText(f"{int(CFG['tamanho'])}%")
        self.viagem_min.setValue(int(CFG["viagem_min"]))
        self.viagem_max.setValue(int(CFG["viagem_max"]))
        self.goddard.setChecked(bool(CFG["goddard"]))
        self.botao.setChecked(bool(CFG["botao_lancar"]))
        self.autostart.setChecked(autostart_enabled())
        self.tela_cheia.setChecked(bool(CFG["esconder_tela_cheia"]))
        self.dormir.setChecked(bool(CFG["dormir"]))
        self.sons.setChecked(bool(CFG["sons"]))
        self.som_jimmy.setChecked(bool(CFG["som_jimmy"]))
        self.som_ronco.setChecked(bool(CFG["som_ronco"]))
        self.som_goddard.setChecked(bool(CFG["som_goddard"]))
        self.som_foguete.setChecked(bool(CFG["som_foguete"]))
        self.vel_foguete.setCurrentIndex(max(0, self.vel_foguete.findData(CFG["vel_foguete"])))
        for kind, (chk, spin) in self.avisos.items():
            chk.setChecked(bool(CFG["aviso_" + kind]))
            spin.setValue(int(CFG["aviso_" + kind + "_min"]))
        self.aviso_dormir.setChecked(bool(CFG["aviso_dormir"]))
        self.avisos_on.setChecked(bool(CFG["avisos"]))
        self.ideias.setChecked(bool(CFG["ideias"]))
        self.foguete_aleatorio.setChecked(bool(CFG["foguete_aleatorio"]))
        self.ausente.setChecked(bool(CFG["ausente"]))
        self.ausente_min.setValue(int(CFG["ausente_min"]))
        self.datas.setChecked(bool(CFG["datas"]))
        self.amigos.setChecked(bool(CFG["amigos"]))
        self.invencoes.setChecked(bool(CFG["invencoes"]))
        self.lhamas.setChecked(bool(CFG["lhamas"]))
        self.passeios.setChecked(bool(CFG["passeios"]))
        self.goddard_pet.setChecked(bool(CFG["goddard_pet"]))
        self.meteoros.setChecked(bool(CFG["meteoros"]))
        self.carregar_notas()
        self.busca_mouse.setChecked(bool(CFG["busca_mouse"]))
        self.consertos.setChecked(bool(CFG["consertos"]))
        self.resgate_lhama.setChecked(bool(CFG["resgate_lhama"]))
        self.divulgar.setChecked(bool(CFG["divulgar"]))
        self.carregar_contagens()
        self.dancar.setChecked(bool(CFG["dancar"]))
        self.curiosidades.setChecked(bool(CFG["curiosidades"]))
        self.idioma.setCurrentIndex(max(0, self.idioma.findData(CFG["idioma"])))
        self.estacoes.setChecked(bool(CFG["estacoes"]))
        self.easter.setChecked(bool(CFG["easter_egg"]))
        self.apps_on.setChecked(bool(CFG["apps_reagir"]))
        self.rede_on.setChecked(bool(CFG["rede"]))
        self.atualizar_on.setChecked(bool(CFG["atualizar"]))
        self.atualizar_auto.setChecked(bool(CFG["atualizar_sozinho"]))
        self.repo.setText(CFG["repo_github"])
        self.carregar_apps()
        self.atualizar_rede_status()
        if self.manager.ultimo_app: self.app_ultimo.setText(f"Último programa usado: {self.manager.ultimo_app}")
        self.monitor.setCurrentIndex(max(0, self.monitor.findData(CFG["monitor"])))
        self.pomo_foco.setValue(int(CFG["pomodoro_foco"]))
        self.pomo_pausa.setValue(int(CFG["pomodoro_pausa"]))
        self.bateria.setChecked(bool(CFG["bateria"]))
        self.frases.setChecked(bool(CFG["frases"]))
        self.clima_on.setChecked(bool(CFG["clima"]))
        self.chuva.setChecked(bool(CFG["chuva_tela"]))
        self.cidade.setText(CFG["cidade"])
        if self.manager.clima: self.mostrar_clima(self.manager.clima)
        self.carregar_conquistas()
        self.tom_noite.setChecked(bool(CFG["tom_noite"]))
        self.carregar_meus()
        # Sugestão de horário: daqui a 1 hora, hora cheia
        self.ml_hora.setTime(QTime.currentTime().addSecs(3600))
        self.aniv_dia.setValue(int(CFG["aniv_dia"]))
        self.aniv_mes.setValue(int(CFG["aniv_mes"]))
        self.som_avisos.setChecked(bool(CFG["som_avisos"]))
        self.atualizar_avisos_on()
        self.volume.setValue(int(CFG["volume"]))
        self.volume_lbl.setText(f"{int(CFG['volume'])}%")
        # Saídas de áudio atuais ("" = a padrão do Windows)
        self.saida.clear()
        self.saida.addItem(tr("Padrão do Windows"), "")
        for d in QMediaDevices.audioOutputs():
            self.saida.addItem(d.description(), d.description())
        idx = self.saida.findData(CFG["saida_som"])
        self.saida.setCurrentIndex(max(0, idx))
        for w in widgets: w.blockSignals(False)

    def mudou_tamanho(self, valor):
        self.tamanho_lbl.setText(f"{self.tamanho.value()}%")
        self.tamanho_gd_lbl.setText(f"{self.tamanho_gd.value()}%")
        self.aplicar_tamanho.start(400)

    def salvar_tamanho(self):
        CFG["tamanho"] = self.tamanho.value()
        CFG["tamanho_goddard"] = self.tamanho_gd.value()
        save_cfg(CFG)
        self.manager.apply_scale()

    def salvar_viagem(self):
        # Mínimo nunca passa do máximo; vale a partir da próxima viagem
        if self.sender() is self.viagem_min and self.viagem_min.value() > self.viagem_max.value():
            self.viagem_max.setValue(self.viagem_min.value())
        if self.sender() is self.viagem_max and self.viagem_max.value() < self.viagem_min.value():
            self.viagem_min.setValue(self.viagem_max.value())
        CFG["viagem_min"] = self.viagem_min.value()
        CFG["viagem_max"] = self.viagem_max.value()
        save_cfg(CFG)

    def salvar_goddard(self, on):
        CFG["goddard"] = on
        save_cfg(CFG)
        self.manager.restart_pets()

    def salvar_botao(self, on):
        CFG["botao_lancar"] = on
        save_cfg(CFG)
        if self.manager.rocket: self.manager.rocket.btn.setVisible(on)

    def salvar_extras(self, *_):
        CFG["vel_foguete"] = self.vel_foguete.currentData()
        CFG["som_jimmy"] = self.som_jimmy.isChecked()
        CFG["som_ronco"] = self.som_ronco.isChecked()
        CFG["som_goddard"] = self.som_goddard.isChecked()
        CFG["som_foguete"] = self.som_foguete.isChecked()
        for kind, (chk, spin) in self.avisos.items():
            CFG["aviso_" + kind] = chk.isChecked()
            CFG["aviso_" + kind + "_min"] = spin.value()
        CFG["aviso_dormir"] = self.aviso_dormir.isChecked()
        CFG["avisos"] = self.avisos_on.isChecked()
        CFG["ideias"] = self.ideias.isChecked()
        CFG["foguete_aleatorio"] = self.foguete_aleatorio.isChecked()
        # Desligou o aleatório: o lugar atual do foguete passa a ser o fixo
        r = self.manager.rocket
        if not CFG["foguete_aleatorio"] and r and CFG.get("foguete_x") is None:
            CFG["foguete_x"] = r.home_x / max(1, r.sw - r.box)
        CFG["ausente"] = self.ausente.isChecked()
        CFG["ausente_min"] = self.ausente_min.value()
        CFG["datas"] = self.datas.isChecked()
        CFG["amigos"] = self.amigos.isChecked()
        CFG["invencoes"] = self.invencoes.isChecked()
        CFG["lhamas"] = self.lhamas.isChecked()
        CFG["passeios"] = self.passeios.isChecked()
        CFG["goddard_pet"] = self.goddard_pet.isChecked()
        CFG["meteoros"] = self.meteoros.isChecked()
        CFG["busca_mouse"] = self.busca_mouse.isChecked()
        CFG["consertos"] = self.consertos.isChecked()
        CFG["resgate_lhama"] = self.resgate_lhama.isChecked()
        CFG["divulgar"] = self.divulgar.isChecked()
        if not CFG["meteoros"]: self.manager.parar_meteoros()
        CFG["dancar"] = self.dancar.isChecked()
        CFG["curiosidades"] = self.curiosidades.isChecked()
        CFG["estacoes"] = self.estacoes.isChecked()
        CFG["apps_reagir"] = self.apps_on.isChecked()
        CFG["atualizar"] = self.atualizar_on.isChecked()
        CFG["atualizar_sozinho"] = self.atualizar_auto.isChecked()
        if CFG["easter_egg"] != self.easter.isChecked():
            CFG["easter_egg"] = self.easter.isChecked()
            self.manager.aplicar_easter()
        if CFG["rede"] != self.rede_on.isChecked():
            CFG["rede"] = self.rede_on.isChecked()
            self.manager.aplicar_rede()
            self.atualizar_rede_status()
        CFG["pomodoro_foco"] = self.pomo_foco.value()
        CFG["pomodoro_pausa"] = self.pomo_pausa.value()
        CFG["bateria"] = self.bateria.isChecked()
        CFG["frases"] = self.frases.isChecked()
        CFG["clima"] = self.clima_on.isChecked()
        CFG["chuva_tela"] = self.chuva.isChecked()
        tom_mudou = CFG.get("tom_noite") != self.tom_noite.isChecked()
        CFG["tom_noite"] = self.tom_noite.isChecked()
        if tom_mudou:
            for pet in self.manager.pets(): pet.refresh_image()
        # Desligou com um amigo na tela: ele se despede
        f = self.manager.friend
        if not CFG["amigos"] and f: f.leave()
        CFG["aniv_dia"] = self.aniv_dia.value()
        CFG["aniv_mes"] = self.aniv_mes.value()
        CFG["som_avisos"] = self.som_avisos.isChecked()
        save_cfg(CFG)
        self.atualizar_avisos_on()
        # Desligou os lembretes com um aviso na tela: fecha
        j = self.manager.jimmy
        if not CFG["avisos"] and j and j.sequence_state == "reminder":
            j.end_reminder()

    def atualizar_avisos_on(self):
        # Com os lembretes desligados, as opções de cada um ficam acinzentadas
        on = self.avisos_on.isChecked()
        for chk, spin in self.avisos.values():
            chk.setEnabled(on)
            spin.setEnabled(on)
        self.aviso_dormir.setEnabled(on)
        self.som_avisos.setEnabled(on)

    def salvar_idioma(self, *_):
        CFG["idioma"] = self.idioma.currentData()
        save_cfg(CFG)
        # Remonta a janela e o menu no idioma novo
        m = self.manager
        if getattr(m, "tray_menu", None): m.tray_menu.retraduzir()
        m.update_menu()
        pos = self.pos()
        self.close()
        self.deleteLater()
        m.config_window = None
        m.open_config()
        m.config_window.move(pos)

    def salvar_monitor(self, *_):
        CFG["monitor"] = self.monitor.currentData()
        save_cfg(CFG)
        self.manager.apply_monitor()

    def buscar_clima(self):
        CFG["cidade"] = self.cidade.text().strip()
        CFG["clima_dia"] = ""   # mostra a previsão na hora, como teste
        save_cfg(CFG)
        if CFG["cidade"]:
            self.clima_status.setText("Buscando...")
            self.manager.forcar_clima = True   # o Jimmy fala a previsão na hora
            self.manager.clima_worker.buscar(CFG["cidade"])
        else:
            self.clima_status.setText("")

    def mostrar_clima(self, d):
        if "erro" in d:
            self.clima_status.setText("⚠️ " + d["erro"])
        else:
            emoji, desc = clima_desc(d["agora"])
            self.clima_status.setText(f"{d['nome']}: agora {emoji} {desc}, {round(d['temp'])}°  "
                                      f"(hoje {round(d['min'])}° a {round(d['max'])}°)")

    def carregar_notas(self):
        self.notas_lista.clear()
        for n in reversed(CFG["notas"]):
            self.notas_lista.addItem(f"{n['data']} — {n['texto']}")
        if not CFG["notas"]:
            self.notas_lista.addItem("(nenhuma nota ainda)")

    def del_nota(self):
        row = self.notas_lista.currentRow()
        if 0 <= row < len(CFG["notas"]):
            del CFG["notas"][len(CFG["notas"]) - 1 - row]
            save_cfg(CFG)
            self.carregar_notas()

    def carregar_meus(self):
        self.ml_lista.clear()
        for l in sorted(CFG["meus_lembretes"], key=lambda l: l["hora"]):
            self.ml_lista.addItem(lembrete_texto(l))
        if not CFG["meus_lembretes"]:
            self.ml_lista.addItem("(nenhum lembrete ainda)")

    def add_meu(self):
        texto = self.ml_texto.text().strip()
        if not texto:
            self.ml_texto.setFocus()
            return
        novo_lembrete(texto, self.ml_hora.time().toString("HH:mm"), self.ml_rep.currentData())
        self.ml_texto.clear()
        self.carregar_meus()

    def del_meu(self):
        item = self.ml_lista.currentItem()
        if not item: return
        for l in CFG["meus_lembretes"]:
            if tr(lembrete_texto(l)) == item.text():
                CFG["meus_lembretes"].remove(l)
                break
        save_cfg(CFG)
        self.carregar_meus()

    def exportar(self):
        destino = os.path.join(os.path.expanduser("~"), "Desktop", "jimmy_pet_config.json")
        path, _ = QFileDialog.getSaveFileName(self, tr("Exportar configurações"), destino, tr("Configurações (*.json)"))
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(CFG, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, tr("Exportar"), tr("Configurações e conquistas salvas! 💾"))
        except OSError as e:
            QMessageBox.warning(self, tr("Exportar"), tr(f"Não deu para salvar:\n{e}"))

    def importar(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("Importar configurações"), os.path.expanduser(tr("~")), tr("Configurações (*.json)"))
        if not path: return
        try:
            with open(path, encoding="utf-8") as f:
                dados = json.load(f)
            if not isinstance(dados, dict): raise ValueError("arquivo inválido")
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, tr("Importar"), tr(f"Não deu para ler o arquivo:\n{e}"))
            return
        CFG.update({k: v for k, v in dados.items() if k in CONFIG_PADRAO})
        CFG["stats"] = dict(CFG.get("stats") or {})
        CFG["conquistas"] = list(CFG.get("conquistas") or [])
        CFG["meus_lembretes"] = [dict(l) for l in (CFG.get("meus_lembretes") or [])]
        save_cfg(CFG)
        self.carregar()
        self.manager.reload_all()
        QMessageBox.information(self, tr("Importar"), tr("Configurações importadas! 📂"))

    def testar_estacao(self):
        tipos = ["outono", "primavera", "neve"]
        self.manager.start_estacao(tipos[self._est_i % 3])
        self._est_i += 1

    def carregar_apps(self):
        self.ap_lista.clear()
        for exe, frase in sorted(CFG["apps"].items()):
            self.ap_lista.addItem(f"{exe}  →  {frase}")

    def add_app(self):
        exe = self.ap_exe.text().strip().lower()
        frase = self.ap_frase.text().strip()
        if not exe or not frase: return
        if not exe.endswith(".exe"): exe += ".exe"
        CFG["apps"][exe] = frase
        save_cfg(CFG)
        self.ap_exe.clear(); self.ap_frase.clear()
        self.carregar_apps()

    def del_app(self):
        item = self.ap_lista.currentItem()
        if not item: return
        CFG["apps"].pop(item.text().split("  →  ")[0], None)
        save_cfg(CFG)
        self.carregar_apps()

    def salvar_repo(self):
        repo = self.repo.text().strip().replace("https://github.com/", "").strip("/")
        if repo != CFG["repo_github"]:
            CFG["repo_github"] = repo
            save_cfg(CFG)
            self.repo.setText(repo)

    def atualizar_rede_status(self):
        r = self.manager.rede
        if not r:
            self.rede_status.setText("Rede desligada")
        else:
            vivos = r.vivos()
            nomes = ", ".join(v["nome"] for v in vivos.values()) or "nenhum ainda"
            self.rede_status.setText(f"PCs com o pet: {nomes}")

    def carregar_contagens(self):
        self.ct_lista.clear()
        hoje = datetime.date.today()
        for c in sorted(CFG["contagens"], key=lambda c: c["data"]):
            dia = datetime.date.fromisoformat(c["data"])
            faltam = (dia - hoje).days
            quando = "é hoje! 🎉" if faltam == 0 else ("amanhã" if faltam == 1 else f"faltam {faltam} dias")
            self.ct_lista.addItem(f"🗓️ {c['nome']} — {dia.strftime('%d/%m/%Y')} ({quando})")
        if not CFG["contagens"]:
            self.ct_lista.addItem("(nenhuma data ainda)")

    def add_contagem(self):
        nome = self.ct_nome.text().strip()
        if not nome:
            self.ct_nome.setFocus()
            return
        CFG["contagens"].append({"nome": nome, "data": self.ct_data.date().toString("yyyy-MM-dd"), "avisado": ""})
        save_cfg(CFG)
        self.ct_nome.clear()
        self.carregar_contagens()

    def del_contagem(self):
        row = self.ct_lista.currentRow()
        ordenadas = sorted(CFG["contagens"], key=lambda c: c["data"])
        if 0 <= row < len(ordenadas):
            CFG["contagens"].remove(ordenadas[row])
            save_cfg(CFG)
            self.carregar_contagens()

    def carregar_conquistas(self):
        self.cq_lista.clear()
        feitas = 0
        for cid, st, alvo, titulo in CONQUISTAS:
            n = CFG["stats"].get(st, 0)
            if cid in CFG["conquistas"]:
                feitas += 1
                self.cq_lista.addItem(f"✅ {titulo}")
            else:
                self.cq_lista.addItem(f"🔒 {titulo}  ({min(n, alvo)}/{alvo})")
        self.cq_resumo.setText(f"🏆 {feitas} de {len(CONQUISTAS)} conquistas")

    def testar_blast(self):
        j = self.manager.jimmy
        if j and j.sequence_state == "normal":
            j.start_blast()

    def testar_festa(self):
        # Cada clique mostra uma comemoração diferente
        j = self.manager.jimmy
        festas = [("Feliz Natal! 🎄", "natal"), ("Feliz Ano Novo! 🎆", "fogos"), ("Feliz Halloween! 🎃", "halloween"),
                  ("Feliz aniversário! 🎂🎉", "confete")]
        if j and j.sequence_state in ("normal", "party"):
            if j.sequence_state == "party": j.end_show()
            j.start_party(*festas[self._festa_i % len(festas)])
            self._festa_i += 1

    def testar_aviso(self):
        j = self.manager.jimmy
        if j and j.sequence_state in ("normal", "reminder"):
            j.end_reminder()
            j.start_reminder(random.choice(["agua", "pausa", "comer", "exercicio"]))

    def salvar_dormir(self, on):
        CFG["dormir"] = on
        save_cfg(CFG)

    def salvar_tela_cheia(self, on):
        CFG["esconder_tela_cheia"] = on
        save_cfg(CFG)

    def salvar_sons(self, *_):
        CFG["sons"] = self.sons.isChecked()
        CFG["volume"] = self.volume.value()
        CFG["saida_som"] = self.saida.currentData() or ""
        self.volume_lbl.setText(f"{self.volume.value()}%")
        save_cfg(CFG)
        if SONS: SONS.aplicar_cfg()

    def restaurar(self):
        guardar = {k: CFG.get(k) for k in ("stats", "conquistas", "cidade")}  # não apaga o progresso
        CFG.clear()
        CFG.update(CONFIG_PADRAO)
        CFG.update(guardar)
        save_cfg(CFG)
        self.carregar()
        if SONS: SONS.aplicar_cfg()
        self.manager.apply_scale()

class TrayManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        global MANAGER, OX, OY
        MANAGER = self
        geo = tela_geo()
        OX, OY = geo.x(), geo.y()
        atualizar_telas()
        self.queue = []          # avisos esperando o Jimmy ficar livre: (tipo, texto, animação, importante)
        self.pomo = None         # {"estado": "foco"/"pausa", "fim": hora}
        self.bat_warned = set()
        self.clima = None
        self.rain_left = 0
        self.timers = []         # "me avise em X min": {"fim", "min", "texto"}
        self.runners = []        # lhamas e Carl atravessando a tela
        self.meteoros_vivos = []
        self.onda = None         # chuva de meteoros em andamento
        self.next_meteoros = time.time() + random.uniform(900, 1800)
        gd_iniciar()
        QTimer.singleShot(10000, self.check_contagens)
        self.medidor = MedidorSom()
        self.musica_t = 0        # segundos seguidos com música tocando
        self.silencio_t = 0
        self.next_lhama = time.time() + random.uniform(300, 900)
        self.rocket = None
        self.jimmy = None
        self.goddard = None
        self.config_window = None
        global SONS
        SONS = Sons()
        global FX, BALL
        FX = Effects()
        BALL = Ball()
        self.setup_tray()
        # Mantém os pets por cima da barra de tarefas
        self.top_timer = QTimer()
        self.top_timer.timeout.connect(self.keep_pets_on_top)
        self.top_timer.start(300)
        # Some quando um jogo/vídeo está em tela cheia
        self.hidden_fs = False
        self.fs_timer = QTimer()
        self.fs_timer.timeout.connect(self.check_fullscreen)
        self.fs_timer.start(1000)
        # Lembretes (água, pausa, comer, exercício)
        self.last_rem = {k: time.time() for k in AVISOS}
        self.rem_check = QTimer()
        self.rem_check.timeout.connect(self.check_reminders)
        self.rem_check.start(15000)
        # Saiu do PC? (mouse e teclado parados)
        self.away = False
        self.away_timer = QTimer()
        self.away_timer.timeout.connect(self.check_away)
        self.away_timer.start(2000)
        # A cada segundo: fila de avisos, Pomodoro, textos do menu
        self.sec_timer = QTimer()
        self.sec_timer.timeout.connect(self.tick_1s)
        self.sec_timer.start(1000)
        # Clima: agora e a cada 30 min
        self.clima_worker = ClimaWorker()
        self.clima_worker.pronto.connect(self.on_clima)
        self.clima_timer = QTimer()
        self.clima_timer.timeout.connect(self.update_clima)
        self.clima_timer.start(30 * 60 * 1000)
        QTimer.singleShot(8000, self.update_clima)
        # Chuva na tela
        self.rain_timer = QTimer()
        self.rain_timer.timeout.connect(self.rain_step)
        # Estações (folhas, pétalas, neve)
        self.estacao_left = 0
        self.estacao_tipo = None
        self.estacao_timer = QTimer()
        self.estacao_timer.timeout.connect(self.estacao_step)
        # Reação aos programas
        self.last_exe = ""
        self.ultimo_app = ""
        self.app_cd = {}
        # Easter egg
        self.teclado = TecladoNeutron(self.on_neutron)
        if CFG["easter_egg"]: self.teclado.ligar()
        # Atualização
        self.nova_versao = None
        self.atualizador = Atualizador()
        self.atualizador.resultado.connect(self.on_update_info)
        self.atualizador.baixado.connect(self.on_baixado)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(lambda: self.check_update())
        self.update_timer.start(6 * 3600 * 1000)
        QTimer.singleShot(30000, lambda: self.check_update())
        # Rede local
        self.rede = None
        self.next_viagem = time.time() + random.uniform(600, 1200)
        self.aplicar_rede()
        # Datas comemorativas (confere ao abrir e a cada minuto)
        self.date_timer = QTimer()
        self.date_timer.timeout.connect(self.check_dates)
        self.date_timer.timeout.connect(self.minute_tick)
        self.date_timer.start(60000)
        QTimer.singleShot(6000, self.check_dates)
        # Visitas dos amigos (primeira em 3 a 8 min, depois a cada 6 a 14 min)
        self.friend = None
        self.last_friend = None
        self.next_friend = time.time() + random.uniform(180, 480)
        self.friend_timer = QTimer()
        self.friend_timer.timeout.connect(self.check_friend)
        self.friend_timer.start(5000)
        self.start_pets()

    def setup_tray(self):
        self.tray = QSystemTrayIcon()
        icon_path = os.path.join(ANIM_DIR, "jimmy_idle", "00.png")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(QIcon.fromTheme("system-information"))
        menu = TMenu()
        self.tray_menu = menu
        self.pomo_action = menu.addAction("🍅 Pomodoro")
        self.pomo_action.triggered.connect(self.toggle_pomodoro)
        self.quiet_action = menu.addAction("🔕 Não perturbe por 1 hora")
        self.quiet_action.triggered.connect(self.toggle_quiet)
        menu.addSeparator()
        launch_action = menu.addAction("🚀 Lançar agora")
        launch_action.triggered.connect(lambda: self.jimmy and self.jimmy.launch_now())
        friend_action = menu.addAction("👫 Chamar um amigo")
        friend_action.triggered.connect(lambda: self.spawn_friend())
        ball_action = menu.addAction("🎾 Bolinha (jogar / guardar)")
        ball_action.triggered.connect(self.toggle_ball)
        self.add_timer_menu(menu)
        self.update_action = menu.addAction("🔄 Atualizar")
        self.update_action.triggered.connect(self.do_update)
        self.update_action.setVisible(False)
        config_action = menu.addAction("⚙️ Configurações")
        config_action.triggered.connect(self.open_config)
        menu.addSeparator()
        restart_action = menu.addAction("🔄 Atualizar Pets")
        restart_action.triggered.connect(self.restart_pets)
        exit_action = menu.addAction("❌ Sair")
        exit_action.triggered.connect(self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def start_pets(self):
        self.rocket = Rocket()
        self.rocket.show()
        self.jimmy = Jimmy(self.rocket)
        self.jimmy.show()
        self.goddard = None
        if CFG["goddard"]:
            self.goddard = Goddard(self.jimmy)
            self.goddard.show()

    def restart_pets(self):
        for r in list(getattr(self, "runners", [])):
            r.shutdown()
        self.runners = []
        if getattr(self, "friend", None):
            self.friend.shutdown()
            self.friend = None
        for pet in (self.goddard, self.jimmy, self.rocket):
            if pet: pet.shutdown()
        if BALL: BALL.held_by = None
        self.start_pets()
        if self.hidden_fs:
            for pet in self.pets(): pet.pause()

    def pets(self):
        fixos = [p for p in (self.rocket, self.jimmy, self.goddard, getattr(self, "friend", None), getattr(self, "carl_resgate", None)) if p]
        return fixos + list(getattr(self, "runners", []))

    def start_resgate(self):
        j = self.jimmy
        if (not j or j.sequence_state != "normal" or j.state == "going" or getattr(self, "carl_resgate", None) or self.hidden_fs
                or self.friend or not Pet.frame(None, "planeta", 0, None) or not j.rocket.isVisible()):
            return
        self.ultima_busca = time.time()
        pl = Planeta(random.uniform(0.25, 0.75) * j.sw)
        self.carl_resgate = CarlResgate(j, self.fim_carl)
        self.carl_resgate.show()
        j.start_resgate(pl)

    def fim_resgate(self, lhama_anim):
        c = getattr(self, "carl_resgate", None)
        if not c: return
        # A lhama desce correndo para o lado em que o Carl vai embora
        lh = Runner(lhama_anim, c.side, random.uniform(5, 6), on_done=self.runner_done)
        lh.x = self.jimmy.x + self.jimmy.box / 2
        lh.show()
        self.runners.append(lh)
        c.feliz()

    def fim_carl(self):
        self.carl_resgate = None

    def start_game(self):
        if getattr(self, "game", None) or not self.jimmy: return
        if FX: FX.clear()
        self.parar_meteoros()
        for pet in self.pets(): pet.pause()
        self.ball_was_visible = bool(BALL and BALL.isVisible())
        if BALL: BALL.hide(); BALL.timer.stop()
        self.hidden_fs = True      # sem avisos, visitas e afins durante o jogo
        self.game = ModoGame(self.fim_game)

    def fim_game(self, pontos, recorde):
        self.game = None
        self.hidden_fs = False
        for pet in self.pets(): pet.resume()
        if BALL and getattr(self, "ball_was_visible", False):
            BALL.show(); BALL.timer.start(30)
        j = self.jimmy
        if j and pontos:
            j.say(f"Fizemos {pontos} pontos! 🕹️" + (" 🏆 Recorde!" if recorde else ""), 100)

    def check_fullscreen(self):
        if getattr(self, "game", None): return   # o próprio jogo ocupa a tela toda
        try:
            fs = CFG["esconder_tela_cheia"] and foreground_is_fullscreen()
        except Exception as e:
            log_error(e)
            fs = False
        if fs and not self.hidden_fs:
            if FX: FX.clear()
            self.parar_meteoros()
            for pet in self.pets(): pet.pause()
            self.ball_was_visible = bool(BALL and BALL.isVisible())
            if BALL: BALL.hide(); BALL.timer.stop()
        elif not fs and self.hidden_fs:
            for pet in self.pets(): pet.resume()
            if BALL and getattr(self, "ball_was_visible", False):
                BALL.show(); BALL.timer.start(30)
        self.hidden_fs = fs

    def start_busca_mouse(self):
        j, g = self.jimmy, self.goddard
        if not j or not g or j.sequence_state != "normal" or g.busca or g.flying: return
        self.ultima_busca = time.time()
        j.trip_timer.stop()
        j.state = "idle"
        j.sequence_state = "busca_mouse"
        j.busca_t = 0
        tocar("brainblast")
        j.say("Tive uma ideia de invenção! 💡 Mas preciso daquele ponteiro...", 90)
        QTimer.singleShot(2800, lambda: j.sequence_state == "busca_mouse" and j.say("Goddard, pega o ponteiro! 🐕", 80))
        g.start_busca()

    def fim_busca_mouse(self, entregou):
        j = self.jimmy
        if not j or j.sequence_state != "busca_mouse": return
        j.sequence_state = "normal"
        j.state = "idle"
        if entregou:
            j.say("Valeu, Goddard! Agora sim, vou inventar! 🛠️", 100)
        else:
            j.say("Opa, você voltou! Pode ficar com o mouse 😅", 90)

    def check_away(self):
        j = self.jimmy
        if not j or self.hidden_fs: return
        idle = idle_seconds()
        # Às vezes, antes do cochilo, o Jimmy tem uma ideia e manda o Goddard buscar o ponteiro
        if ((CFG["busca_mouse"] or CFG["resgate_lhama"]) and not self.away and idle >= 600 and not getattr(self, "busca_decidida", False)
                and j.sequence_state == "normal" and j.state != "going" and not quieto()):
            self.busca_decidida = True
            if random.random() < 0.3 and time.time() - getattr(self, "ultima_busca", 0) > 3600:
                # Sorteia entre o Goddard buscar o ponteiro e o resgate da lhama no planeta
                opcoes = []
                if self.goddard and not self.goddard.flying and self.goddard.isVisible(): opcoes.append(self.start_busca_mouse)
                if CFG["resgate_lhama"]: opcoes.append(self.start_resgate)
                if opcoes:
                    random.choice(opcoes)()
                    return
        if idle < 3: self.busca_decidida = False
        if (CFG["ausente"] and not self.away and idle >= CFG["ausente_min"] * 60
                and j.sequence_state == "normal" and j.state != "going"):
            self.away = True
            j.start_sleep("ausente")
        elif self.away and idle < 3:
            # Você voltou
            self.away = False
            if j.sequence_state == "sleeping" and j.sleep_kind == "ausente":
                j.greet = True
                j.wake_up()

    # ---------------- fila, Pomodoro, não perturbe ----------------
    def check_musica(self):
        j = self.jimmy
        if not j or self.hidden_fs: return
        if j.sequence_state == "danca" and time.time() < getattr(j, "danca_ate", 0):
            return
        if getattr(j, "danca_ate", 0) and j.sequence_state == "danca":
            j.danca_ate = 0
            j.end_danca()
            return
        if not CFG["dancar"]:
            if j.sequence_state == "danca": j.end_danca()
            return
        tocando = self.medidor.pico() > 0.03 and not (SONS and SONS.tocando_algo())
        if tocando:
            self.musica_t += 1
            self.silencio_t = 0
        else:
            self.silencio_t += 1
            if self.silencio_t >= 2: self.musica_t = 0
        if j.sequence_state == "danca":
            if self.silencio_t >= 3: j.end_danca()      # música parou
        elif self.musica_t >= 4 and j.sequence_state == "normal" and j.state != "going" and not nao_perturbe():
            j.start_danca()

    def tick_1s(self):
        self.check_musica()
        self.check_jogo_bola()
        self.check_apps()
        self.sec_count = getattr(self, "sec_count", 0) + 1
        if self.rede and self.sec_count % 10 == 0: self.rede.anunciar()
        self.check_timers()
        self.check_meus_lembretes()
        self.update_pomo()
        self.process_queue()
        self.update_menu()

    # ---------------- timer rápido ----------------
    def start_timer(self, minutos, texto=None):
        self.timers.append({"fim": time.time() + minutos * 60, "min": minutos, "texto": texto})
        if self.jimmy: self.jimmy.say(f"Beleza! Te aviso em {minutos} min. ⏱️", 80)

    def ask_timer(self):
        minutos, ok = QInputDialog.getInt(None, tr("Me avise em..."), tr("Daqui a quantos minutos?"), 20, 1, 600)
        if not ok: return
        texto, ok = QInputDialog.getText(None, tr("Me avise em..."), tr("Mensagem (opcional):"))
        self.start_timer(minutos, texto.strip() if ok and texto.strip() else None)

    def cancel_timers(self):
        self.timers = []
        if self.jimmy: self.jimmy.say("Timers cancelados. ⏱️", 70)

    def check_timers(self):
        agora = time.time()
        for t in [t for t in self.timers if agora >= t["fim"]]:
            self.timers.remove(t)
            msg = t["texto"] or "Deu o tempo!"
            self.queue.append(("timer", f"⏰ {msg} ({t['min']} min)", "ideia_susto", True))

    def fill_timer_menu(self, sub):
        sub.clear()
        for m in (5, 10, 15, 30, 60):
            sub.addAction(f"{m} minutos", lambda _=False, m=m: self.start_timer(m))
        sub.addAction("Outro tempo...", self.ask_timer)
        if self.timers:
            sub.addSeparator()
            for t in self.timers:
                faltam = max(1, int((t["fim"] - time.time() + 59) // 60))
                a = sub.addAction(f"⏳ {t['texto'] or 'Timer'}: faltam {faltam} min")
                a.setEnabled(False)
            sub.addAction(f"❌ Cancelar timers ({len(self.timers)})", self.cancel_timers)

    def add_timer_menu(self, menu):
        sub = menu.addMenu("⏱️ Me avise em...")
        sub.aboutToShow.connect(lambda: self.fill_timer_menu(sub))
        self.fill_timer_menu(sub)
        return sub

    # ---------------- lembretes personalizados ----------------
    def check_meus_lembretes(self):
        tm = time.localtime()
        hm = time.strftime("%H:%M", tm)
        chave = time.strftime("%Y-%m-%d %H:%M", tm)
        mudou = False
        for l in list(CFG["meus_lembretes"]):
            if l.get("hora") == hm and lembrete_hoje(l, tm) and l.get("ultimo") != chave:
                l["ultimo"] = chave
                self.queue.append(("meu", f"📝 {l['texto']}", "ideia_ideia", True))
                if l.get("rep") == "uma":
                    CFG["meus_lembretes"].remove(l)   # lembrete de uma vez só: some depois de avisar
                mudou = True
        if mudou:
            save_cfg(CFG)
            if self.config_window and self.config_window.isVisible():
                self.config_window.carregar_meus()

    # ---------------- menu do clique no Jimmy ----------------
    def menu_clique(self, pos):
        j, g = self.jimmy, self.goddard
        menu = TMenu()
        menu.addAction("🎾 Brincar de bolinha com o Goddard", self.brincar_bolinha)
        menu.addAction("📝 Novo lembrete...", self.dialogo_lembrete)
        self.add_timer_menu(menu)
        prox = menu.addMenu("📋 Próximos lembretes")
        agora, tm = time.strftime("%H:%M"), time.localtime()
        hoje = sorted((l for l in CFG["meus_lembretes"] if lembrete_hoje(l, tm) and l["hora"] > agora), key=lambda l: l["hora"])
        for l in hoje[:3]:
            prox.addAction(f"⏰ {l['hora']} — {l['texto']}").setEnabled(False)
        if not hoje:
            prox.addAction("(nenhum para hoje)").setEnabled(False)
        prox.addSeparator()
        prox.addAction("⚙️ Ver todos", self.open_config)
        menu.addSeparator()
        jogos = menu.addMenu("🎮 Brincar")
        jogos.addAction("🕹️ Modo Game", self.start_game)
        jogos.addAction("🚀 Decolar agora", lambda: j and j.launch_now())
        jogos.addAction("🛸 Passeio de foguete", lambda: j and j.go_to_rocket(passeio=True))
        jogos.addAction("🔧 Consertar o foguete", lambda: j and j.go_to_rocket(conserto=True))
        jogos.addAction("🪐 Resgatar a lhama do planeta", self.start_resgate)
        jogos.addAction("☄️ Chuva de meteoros", self.start_meteoros)
        jogos.addAction("🖱️ Goddard, pega o ponteiro!", self.start_busca_mouse)
        jogos.addAction("💃 Dançar", self.dancar_agora)
        jogos.addAction("🧪 Inventar algo", lambda: j and j.sequence_state == "normal" and j.start_invencao())
        if g and CFG["goddard_pet"]:
            sub = menu.addMenu("🐶 Goddard")
            sub.addAction("🛢️ Dar óleo", lambda: g.cuidar("oleo"))
            sub.addAction("🛁 Dar banho", lambda: g.cuidar("banho"))
            sub.addAction("🎾 Brincar", lambda: g.cuidar("brincar"))
        menu.addSeparator()
        menu.addAction("🗒️ Nota rápida...", self.nota_rapida)
        menu.addAction("🎲 Decida por mim...", self.decida_por_mim)
        menu.addAction("💧 Bebi água!", self.bebi_agua)
        menu.exec(pos)

    def brincar_bolinha(self):
        """O Jimmy joga, o Goddard traz; cada vez mais longe, de 2 a 5 rodadas."""
        j, g = self.jimmy, self.goddard
        if not BALL or not j or not g or not g.isVisible() or getattr(self, "jogo_bola", None): return
        self.jogo_bola = {"rodadas": random.randint(2, 5), "feitas": 0}
        self.jogar_bola()

    def jogar_bola(self):
        jb, j = self.jogo_bola, self.jimmy
        if not jb or not j: return
        if j.sequence_state != "normal" or j.in_air:
            QTimer.singleShot(1500, self.jogar_bola)   # ocupado: joga quando terminar
            return
        k = vel()
        lado = 1 if j.x + j.box / 2 < j.sw / 2 else -1   # para o lado com mais espaço
        espaco = (j.sw - j.x - j.box) if lado == 1 else j.x
        frac = 0.3 + 0.65 * jb["feitas"] / max(1, jb["rodadas"] - 1)   # cada vez mais longe
        j.direction = lado
        j.vx = 0.0
        j.state = "idle"
        BALL.arremessar(j.x + j.box / 2 + lado * j.box * 0.3, j.y + j.box * 0.45,
                        lado * max(4 * k, espaco * frac / 48), -random.uniform(9, 12) * k)
        tocar("bolinha")
        jb["feitas"] += 1
        frases = ["Vai buscar, Goddard! 🎾", "Mais longe agora! 💪", "Laaaaá longe! 🚀", "Essa foi longe! 😄", "Última! Vai! 🎾"]
        j.say(frases[-1] if jb["feitas"] == jb["rodadas"] and jb["rodadas"] > 2 else frases[min(jb["feitas"] - 1, 3)], 60)

    def check_jogo_bola(self):
        jb = getattr(self, "jogo_bola", None)
        if not jb: return
        g, j = self.goddard, self.jimmy
        if not BALL.isVisible() or not g or not j:
            self.jogo_bola = None   # guardaram a bolinha
            return
        # O Goddard trouxe e soltou na frente do Jimmy
        if not BALL.thrown and BALL.held_by is None and g.fetch is None:
            if jb["feitas"] < jb["rodadas"]:
                jb["feitas_espera"] = jb.get("feitas_espera", 0) + 1
                if jb["feitas_espera"] >= 2:          # um segundinho de festa antes do próximo
                    jb["feitas_espera"] = 0
                    self.jogar_bola()
            else:
                self.jogo_bola = None
                j.say("Ufa, cansei! Boa, Goddard! 🐕", 90)
                QTimer.singleShot(5000, lambda: BALL.isVisible() and not getattr(self, "jogo_bola", None) and BALL.put_away())

    def dancar_agora(self):
        j = self.jimmy
        if not j or j.sequence_state != "normal": return
        j.danca_ate = time.time() + 15
        j.start_danca()

    def dialogo_lembrete(self):
        d = QDialog()
        d.setWindowTitle(tr("📝 Novo lembrete"))
        d.setWindowFlags(d.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        f = QFormLayout(d)
        texto = QLineEdit(); texto.setPlaceholderText(tr("ex.: Reunião com a equipe"))
        hora = QTimeEdit(QTime.currentTime().addSecs(3600)); hora.setDisplayFormat("HH:mm")
        repete = QComboBox()
        for key, nome in REPETICOES: repete.addItem(tr(nome), key)
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(d.accept); botoes.rejected.connect(d.reject)
        f.addRow(tr("Lembrete:"), texto)
        f.addRow(tr("Quando:"), hora)
        f.addRow("", repete)
        f.addRow(botoes)
        if d.exec() != QDialog.DialogCode.Accepted or not texto.text().strip(): return
        l = novo_lembrete(texto.text().strip(), hora.time().toString("HH:mm"), repete.currentData())
        if self.jimmy: self.jimmy.say(f"Anotado! 📝 Te lembro às {l['hora']}.", 90)
        if self.config_window and self.config_window.isVisible(): self.config_window.carregar_meus()

    def nota_rapida(self):
        texto, ok = QInputDialog.getText(None, tr("🗒️ Nota rápida"), tr("O que eu anoto?"))
        if not ok or not texto.strip(): return
        CFG["notas"].append({"texto": texto.strip(), "data": time.strftime("%d/%m %H:%M")})
        save_cfg(CFG)
        if self.jimmy: self.jimmy.say("Guardei a nota! 🗒️ Fica em Configurações → 📝 Meus.", 90)
        if self.config_window and self.config_window.isVisible(): self.config_window.carregar_notas()

    def decida_por_mim(self):
        texto, ok = QInputDialog.getText(None, tr("🎲 Decida por mim"), tr("Opções separadas por vírgula:"))
        opcoes = [o.strip() for o in texto.replace(";", ",").split(",") if o.strip()] if ok else []
        j = self.jimmy
        if not opcoes or not j: return
        tocar("brainblast")
        j.say(f"⚡ Calculando... Escolhi: {random.choice(opcoes)}! 🎲", 110)

    def bebi_agua(self):
        hoje = time.strftime("%Y-%m-%d")
        a = CFG["agua_hoje"]
        if a.get("dia") != hoje: a.clear(); a.update({"dia": hoje, "n": 0})
        a["n"] += 1
        save_cfg(CFG)
        stat("copos")
        if self.jimmy: self.jimmy.say(f"💧 Boa! {a['n']} copo(s) de água hoje.", 80)

    # ---------------- menu do botão direito ----------------
    def quick_menu(self, pos, alvo=None):
        menu = TMenu()
        j = self.jimmy
        g = self.goddard
        if alvo is not None and alvo is g and CFG["goddard_pet"]:
            menu.addAction("🛢️ Dar óleo", lambda: g.cuidar("oleo"))
            menu.addAction("🎾 Brincar", lambda: g.cuidar("brincar"))
            menu.addAction("🛁 Dar banho", lambda: g.cuidar("banho"))
            menu.addSeparator()
        menu.addAction("🚀 Lançar o foguete", lambda: j and j.launch_now())
        menu.addAction("🎾 Bolinha", self.toggle_ball)
        menu.addAction("👫 Chamar um amigo", lambda: self.spawn_friend())
        menu.addAction("🧪 Inventar algo", lambda: j and j.sequence_state == "normal" and j.start_invencao())
        menu.addAction("🦙 Soltar as lhamas", self.solta_lhamas)
        menu.addAction("🛸 Passeio de foguete", lambda: j and j.go_to_rocket(passeio=True))
        menu.addAction("🔧 Consertar o foguete", lambda: j and j.go_to_rocket(conserto=True))
        menu.addAction("☄️ Chuva de meteoros", lambda: self.start_meteoros())
        menu.addAction("🕹️ Modo Game", self.start_game)
        menu.addAction("🖱️ Goddard, pega o ponteiro!", self.start_busca_mouse)
        menu.addAction("⚡ Brain Blast", lambda: j and j.sequence_state == "normal" and j.start_blast())
        menu.addSeparator()
        menu.addAction(self.pomo_action.text(), self.toggle_pomodoro)
        self.add_timer_menu(menu)
        menu.addAction(self.quiet_action.text(), self.toggle_quiet)
        menu.addSeparator()
        if self.nova_versao:
            menu.addAction(self.update_action.text(), self.do_update)
        if self.rede and self.rede.vivos():
            menu.addAction("📡 Visitar outro PC", self.visitar_agora)
        menu.addAction("⚙️ Configurações", self.open_config)
        menu.exec(pos)

    def reload_all(self):
        # Depois de importar configurações: monitor, tamanho e sons novos
        global OX, OY, ESCALA
        geo = tela_geo()
        OX, OY = geo.x(), geo.y()
        atualizar_telas()
        ESCALA = CFG["tamanho"] / 100
        Pet.box_cache.clear()
        if SONS: SONS.aplicar_cfg()
        if FX: FX.clear()
        if BALL:
            BALL.put_away()
            BALL.sw, BALL.sh = geo.width(), geo.height()
        self.restart_pets()

    def process_queue(self):
        j = self.jimmy
        if not self.queue or not j or self.hidden_fs: return
        # Importantes (Pomodoro, bateria) passam na frente
        idx = next((i for i, q in enumerate(self.queue) if q[3]), 0)
        kind, text, anim, importante = self.queue[idx]
        if quieto() and not importante: return
        if j.can_remind():
            self.queue.pop(idx)
            if kind == "party":
                j.start_party(text, anim)
            else:
                j.start_reminder(kind, text, anim)

    def toggle_pomodoro(self):
        j = self.jimmy
        if self.pomo:
            self.pomo = None
            if j: j.say("Pomodoro parado. 🍅", 80)
        else:
            self.pomo = {"estado": "foco", "fim": time.time() + CFG["pomodoro_foco"] * 60}
            if j: j.say(f"Foco por {CFG['pomodoro_foco']} min! 🍅", 100)
            if self.friend: self.friend.leave()
        self.update_menu()

    def update_pomo(self):
        if not self.pomo or time.time() < self.pomo["fim"]: return
        if self.pomo["estado"] == "foco":
            stat("focos")
            self.pomo = {"estado": "pausa", "fim": time.time() + CFG["pomodoro_pausa"] * 60}
            self.queue.append(("pomodoro", f"Hora da pausa! ☕ Descansa {CFG['pomodoro_pausa']} min.", "aviso_pausa", True))
        else:
            self.pomo = {"estado": "foco", "fim": time.time() + CFG["pomodoro_foco"] * 60}
            self.queue.append(("pomodoro", "Fim da pausa! Bora focar? 🍅", "ideia_ideia", True))

    def toggle_quiet(self):
        global QUIET_UNTIL
        if nao_perturbe():
            QUIET_UNTIL = 0.0
        else:
            QUIET_UNTIL = time.time() + 3600
            if self.friend: self.friend.leave()
        self.update_menu()

    def update_menu(self):
        if not hasattr(self, "pomo_action"): return
        if self.pomo:
            mins = max(1, int((self.pomo["fim"] - time.time() + 59) // 60))
            nome = "🍅 Foco" if self.pomo["estado"] == "foco" else "☕ Pausa"
            self.pomo_action.setText(tr(f"{tr(nome)}: {mins} min (clique para parar)"))
        else:
            self.pomo_action.setText(tr(f"🍅 Pomodoro ({CFG['pomodoro_foco']} min de foco)"))
        if nao_perturbe():
            self.quiet_action.setText(tr(f"🔔 Reativar (silêncio até {time.strftime('%H:%M', time.localtime(QUIET_UNTIL))})"))
        else:
            self.quiet_action.setText(tr("🔕 Não perturbe por 1 hora"))

    # ---------------- bateria, clima, chuva ----------------
    # ---------------- estações ----------------
    def start_estacao(self, tipo=None):
        self.estacao_tipo = tipo or estacao_atual()
        if not self.estacao_tipo: return
        self.estacao_left = 140   # ~20 s
        self.estacao_timer.start(150)

    def estacao_step(self):
        j = self.jimmy
        if self.estacao_left <= 0 or not FX or not j or self.hidden_fs:
            self.estacao_timer.stop()
            return
        self.estacao_left -= 1
        cx = j.x + j.box / 2
        topo = max(0, j.y - 350)
        if self.estacao_tipo == "outono":
            FX.folhas(cx - 500, cx + 500, topo, 1, [(205, 110, 30), (170, 70, 20), (230, 170, 40), (140, 90, 40)])
        elif self.estacao_tipo == "primavera":
            FX.folhas(cx - 500, cx + 500, topo, 1, [(255, 182, 193), (255, 105, 180), (255, 240, 245), (255, 200, 220)])
        else:
            FX.snow(cx - 500, cx + 500, topo, 2)

    # ---------------- reação aos programas ----------------
    def check_apps(self):
        if self.sec_count_apps() % 2: return
        exe = exe_em_foco()
        if not exe or exe == self.last_exe: return
        self.last_exe = exe
        if exe not in ("jimmyneutronpet.exe", "python.exe", "pythonw.exe", "explorer.exe"):
            self.ultimo_app = exe
            if self.config_window and self.config_window.isVisible():
                self.config_window.app_ultimo.setText(f"Último programa usado: {exe}")
        frase = {k.lower(): v for k, v in CFG["apps"].items()}.get(exe)
        j = self.jimmy
        if (frase and CFG["apps_reagir"] and j and j.sequence_state == "normal" and j.say_timer == 0
                and not quieto() and time.time() - self.app_cd.get(exe, 0) > 600):
            self.app_cd[exe] = time.time()
            j.say(frase, 110)

    def sec_count_apps(self):
        return getattr(self, "sec_count", 0)

    # ---------------- easter egg ----------------
    def on_neutron(self):
        j = self.jimmy
        if j and j.sequence_state == "normal":
            j.start_blast()

    def aplicar_easter(self):
        if CFG["easter_egg"]: self.teclado.ligar()
        else: self.teclado.desligar()

    # ---------------- atualização ----------------
    def check_update(self, manual=False):
        repo = CFG["repo_github"].strip().strip("/")
        self.update_manual = manual
        if not repo or (not manual and not CFG["atualizar"]):
            if manual and self.config_window: self.config_window.upd_status.setText("Informe o repositório (usuario/nome).")
            return
        if manual and self.config_window: self.config_window.upd_status.setText("Procurando...")
        self.atualizador.verificar(repo)

    def on_update_info(self, d):
        cw = self.config_window
        if "erro" in d:
            if cw: cw.upd_status.setText("⚠️ " + d["erro"])
            return
        if versao_tupla(d["versao"]) > versao_tupla(APP_VERSAO) and d.get("url"):
            self.nova_versao = d
            if CFG["atualizar_sozinho"] and getattr(sys, "frozen", False):
                # Atualiza sem perguntar: baixa, troca o .exe e reabre
                if cw: cw.upd_status.setText(f"⬇️ Atualizando para v{d['versao']}...")
                if self.jimmy: self.jimmy.say(f"Atualizando para a v{d['versao']}... ⏬", 300)
                self.atualizador.baixar(d["url"], sys.executable + ".new")
                return
            self.update_action.setText(tr(f"🔄 Atualizar para v{d['versao']}"))
            self.update_action.setVisible(True)
            if cw: cw.upd_status.setText(f"🎉 Versão nova disponível: v{d['versao']}")
            if CFG.get("avisou_versao") != d["versao"] and self.jimmy:
                CFG["avisou_versao"] = d["versao"]
                save_cfg(CFG)
                self.queue.append(("update", f"Tem versão nova! v{d['versao']} 🎉 Clique em mim com o botão direito → Atualizar",
                                   "ideia_ideia", False))
        elif cw:
            cw.upd_status.setText(f"✅ Você já tem a versão mais nova (v{APP_VERSAO}).")

    def do_update(self):
        d = self.nova_versao
        if not d: return
        if not getattr(sys, "frozen", False):
            QMessageBox.information(None, tr("Atualizar"), tr("A atualização automática funciona só no .exe."))
            return
        if QMessageBox.question(None, tr("Atualizar"), tr(f"Baixar e instalar a versão {d['versao']}?\nO pet reabre sozinho.")) \
                != QMessageBox.StandardButton.Yes:
            return
        if self.jimmy: self.jimmy.say("Baixando a versão nova... ⏬", 300)
        self.atualizador.baixar(d["url"], sys.executable + ".new")

    def on_baixado(self, d):
        if "erro" in d:
            QMessageBox.warning(None, tr("Atualizar"), tr("Não deu para atualizar: ") + d["erro"])
            return
        exe = sys.executable
        try:
            if os.path.exists(exe + ".old"): os.remove(exe + ".old")
            os.rename(exe, exe + ".old")        # o .exe em uso pode ser renomeado, não apagado
            os.rename(d["arquivo"], exe)
        except OSError as e:
            QMessageBox.warning(None, tr("Atualizar"), tr(f"Não deu para trocar o arquivo:\n{e}"))
            return
        subprocess.Popen([exe], creationflags=0x00000008 | 0x00000200)
        self.quit_app()

    # ---------------- rede local ----------------
    def aplicar_rede(self):
        if CFG["rede"] and not self.rede:
            self.rede = Rede(self.on_rede)
            self.rede.anunciar()
        elif not CFG["rede"] and self.rede:
            self.rede.fechar()
            self.rede = None

    def on_rede(self, msg):
        tipo = msg.get("tipo")
        j = self.jimmy
        if tipo == "visita":
            livre = (j and j.sequence_state == "normal" and j.state != "going" and not self.friend
                     and not self.hidden_fs and not quieto())
            if not livre:
                self.rede.enviar({"tipo": "ocupado", "para": msg["de"]})
                return
            self.rede.enviar({"tipo": "chegou", "para": msg["de"]})
            Visitante.origem_nome = msg.get("nome", "?")
            origem = msg["de"]
            def volta(friend, origem=origem):
                self.friend_done(friend)
                if self.rede: self.rede.enviar({"tipo": "volta", "para": origem})
            j.state = "idle"
            self.friend = Visitante("visitante", j, volta)
            self.friend.show()
        elif tipo == "chegou" and j and getattr(j, "viagem", None):
            j.viagem["ack"] = True
        elif tipo == "ocupado" and j and getattr(j, "viagem", None):
            j.voltar_viagem("O Jimmy de lá tá ocupado! 😅")
        elif tipo == "volta" and j and getattr(j, "viagem", None):
            j.voltar_viagem(f"Voltei! O PC do {msg.get('nome', '?')} é legal! 😄")

    def visitar_agora(self):
        j = self.jimmy
        vivos = self.rede.vivos() if self.rede else {}
        if not vivos:
            if j: j.say("Não achei nenhum PC com o pet na rede. 📡", 90)
            return
        if j and j.sequence_state == "normal":
            pid, info = random.choice(list(vivos.items()))
            j.start_viagem(pid, info["nome"])
            self.next_viagem = time.time() + random.uniform(900, 1800)

    def check_canal(self):
        if not CFG["divulgar"]: return
        agora = time.time()
        if not CFG["divulga_prox"]:
            CFG["divulga_prox"] = agora + random.uniform(12, 36) * 3600
            save_cfg(CFG)
        elif agora >= CFG["divulga_prox"] and not quieto() and not self.hidden_fs:
            self.queue.append(("canal", random.choice(FRASES_CANAL), "ideia_feliz", False))
            CFG["divulga_prox"] = agora + random.uniform(12, 36) * 3600
            save_cfg(CFG)

    def minute_tick(self):
        self.check_battery()
        self.check_canal()
        if SONS: SONS.verificar_saida()
        self.check_contagens()
        # Goddard: os medidores caem com o tempo
        if CFG["goddard_pet"]:
            for k, q in GD_QUEDA.items(): gd_add(k, -q)
            CFG["gd_stats"]["ts"] = time.time()
            save_cfg(CFG)
        # Estação do ano: uma "chuvinha" de folhas/pétalas/neve a cada ~10 min
        if (CFG["estacoes"] and estacao_atual() and int(time.time() // 60) % 10 == 5 and not self.rain_timer.isActive()
                and not self.hidden_fs and not quieto()):
            self.start_estacao()
        for pet in self.pets(): pet.refresh_image()   # tom de noite
        # Chovendo de verdade: uma pancadinha na tela a cada ~4 min
        c = self.clima
        if (c and "erro" not in c and CFG["chuva_tela"] and chovendo(c["agora"]) and not self.hidden_fs
                and int(time.time() // 60) % 4 == 0):
            self.start_rain()

    def check_battery(self):
        if not CFG["bateria"]: return
        b = bateria()
        if b is None: return
        pct, tomada = b
        if tomada:
            self.bat_warned.clear()
            return
        for nivel in (10, 20):
            if pct <= nivel and nivel not in self.bat_warned:
                self.bat_warned.update(n for n in (10, 20) if n >= nivel)
                self.queue.append(("bateria", f"🔋 Bateria em {pct}%! Liga o carregador! ⚡", "ideia_susto", True))
                break

    def update_clima(self):
        if CFG["clima"] and CFG["cidade"].strip():
            self.clima_worker.buscar(CFG["cidade"].strip())

    def on_clima(self, d):
        self.clima = d
        if self.config_window: self.config_window.mostrar_clima(d)
        if "erro" in d or not CFG["clima"]: return
        hoje = time.strftime("%Y-%m-%d")
        forcar = getattr(self, "forcar_clima", False)
        self.forcar_clima = False
        if forcar or (CFG.get("clima_dia") != hoje and time.localtime().tm_hour >= 6):
            CFG["clima_dia"] = hoje
            save_cfg(CFG)
            self.queue.append(("clima", texto_clima(d), "ideia_ideia", False))
        if chovendo(d["agora"]) and CFG["chuva_tela"]:
            self.start_rain()

    def start_rain(self):
        self.rain_left = 250   # ~25 s
        self.rain_timer.start(100)
        if self.jimmy: self.jimmy.open_umbrella()

    def rain_step(self):
        j = self.jimmy
        if self.rain_left <= 0 or not FX or not j or self.hidden_fs:
            self.rain_timer.stop()
            if j: j.close_umbrella()   # parou de chover
            return
        self.rain_left -= 1
        cx = j.x + j.box / 2
        FX.rain(cx - 500, cx + 500, 6, j.sh - 10)

    def apply_monitor(self):
        global OX, OY
        geo = tela_geo()
        OX, OY = geo.x(), geo.y()
        atualizar_telas()
        if FX: FX.clear()
        if BALL:
            BALL.put_away()
            BALL.sw, BALL.sh = geo.width(), geo.height()
        self.restart_pets()

    def check_dates(self):
        j = self.jimmy
        if not CFG["datas"] or not j or self.hidden_fs or quieto(): return
        hoje = time.strftime("%Y-%m-%d")
        if CFG.get("comemorado") == hoje: return
        evento = data_especial(time.localtime())
        if evento and j.can_remind():
            stat("festas")
            j.start_party(*evento)
            CFG["comemorado"] = hoje
            save_cfg(CFG)

    def solta_lhamas(self):
        # Uma lhama passa correndo... e o Carl vem logo atrás
        if self.runners or self.hidden_fs: return
        stat("lhamas")
        lado = random.choice([-1, 1])
        lhama = Runner(random.choice(["lhama_marrom", "lhama_branca"]), lado, random.uniform(8, 10),
                       on_done=self.runner_done)
        lhama.show()
        self.runners.append(lhama)
        def carl():
            c = Runner("carl_desespero", lado, random.uniform(6.5, 7.5),
                       fala=random.choice(["Minhas lhamas! 🦙", "Volta aqui, lhaminha! 😱", "Alguém segura essa lhama! 🦙"]),
                       on_done=self.runner_done)
            c.show()
            self.runners.append(c)
        QTimer.singleShot(1600, carl)
        self.next_lhama = time.time() + random.uniform(600, 1500)

    def runner_done(self, r):
        if r in self.runners: self.runners.remove(r)

    def check_viagem(self):
        j = self.jimmy
        if (self.rede and self.rede.vivos() and time.time() >= self.next_viagem and j and j.sequence_state == "normal"
                and j.state != "going" and not self.friend and not quieto() and not self.hidden_fs):
            self.visitar_agora()

    # ---------------- chuva de meteoros ----------------
    def start_meteoros(self):
        j = self.jimmy
        if self.onda or not j or self.hidden_fs: return
        self.onda = {"total": random.randint(6, 10), "lancados": 0, "acertos": 0, "fim": 0}
        self.next_meteoros = time.time() + random.uniform(1200, 2400)
        if j.sequence_state == "normal": j.say("Chuva de meteoros! Clica neles! ☄️", 100)
        QTimer.singleShot(1800, self.lancar_meteoro)

    def lancar_meteoro(self):
        o, j = self.onda, self.jimmy
        if not o or not j or self.hidden_fs: return
        o["lancados"] += 1
        alvo = j.x + j.box / 2 + random.uniform(-220, 220)
        x = alvo + random.uniform(-500, 500)
        chao = (chao_em(alvo) or j.sh) - 12
        self.meteoros_vivos.append(Meteoro(max(20, min(x, j.sw - 20)), alvo, chao, self.meteoro_fim))
        if o["lancados"] < o["total"]:
            QTimer.singleShot(int(random.uniform(1000, 2000)), self.lancar_meteoro)

    def meteoro_fim(self, met, acertou):
        if met in self.meteoros_vivos: self.meteoros_vivos.remove(met)
        o = self.onda
        if not o: return
        if acertou:
            o["acertos"] += 1
            stat("meteoros")
        o["fim"] += 1
        if o["fim"] >= o["total"]:
            a, t = o["acertos"], o["total"]
            self.onda = None
            novo = a > CFG.get("meteoros_recorde", 0)
            if novo:
                CFG["meteoros_recorde"] = a
                save_cfg(CFG)
            j = self.jimmy
            if a == t: texto = f"Você salvou o dia! {a}/{t} ☄️ Perfeito!"
            elif a >= t / 2: texto = f"Boa! Você pegou {a}/{t} meteoros! ☄️"
            else: texto = f"Ufa... só {a}/{t}. Na próxima a gente pega! ☄️"
            if novo and a: texto += " 🏆 Recorde!"
            if j: self.queue.append(("meteoros", texto, "ideia_feliz" if a >= t / 2 else "ideia_susto", True))

    def parar_meteoros(self):
        for m in list(self.meteoros_vivos):
            m.timer.stop(); m.close()
        self.meteoros_vivos = []
        self.onda = None

    # ---------------- contagem regressiva ----------------
    def check_contagens(self):
        hoje = datetime.date.today()
        mudou = False
        for c in list(CFG["contagens"]):
            try:
                dia = datetime.date.fromisoformat(c["data"])
            except ValueError:
                continue
            faltam = (dia - hoje).days
            if faltam < 0:
                CFG["contagens"].remove(c)   # já passou
                mudou = True
                continue
            if c.get("avisado") == hoje.isoformat() or time.localtime().tm_hour < 8:
                continue
            if faltam == 0:
                self.queue.append(("party", f"🎉 Chegou o dia: {c['nome']}!", "confete", False))
            elif faltam == 1:
                self.queue.append(("contagem", f"⏳ Amanhã é o dia: {c['nome']}! 🎉", "ideia_ideia", False))
            elif faltam <= 7 or faltam in (30, 15, 10) or faltam % 7 == 0:
                self.queue.append(("contagem", f"⏳ Faltam {faltam} dias para: {c['nome']}!", "ideia_ideia", False))
            else:
                continue
            c["avisado"] = hoje.isoformat()
            mudou = True
        if mudou:
            save_cfg(CFG)
            if self.config_window and self.config_window.isVisible(): self.config_window.carregar_contagens()

    def check_friend(self):
        if (CFG["meteoros"] and not self.onda and time.time() >= self.next_meteoros and not quieto()
                and not self.hidden_fs and self.jimmy and self.jimmy.sequence_state == "normal"):
            self.start_meteoros()
        self.check_viagem()
        if (CFG["lhamas"] and not quieto() and not self.hidden_fs and not self.runners
                and time.time() >= self.next_lhama and self.jimmy and self.jimmy.sequence_state != "visit"):
            self.solta_lhamas()
        j = self.jimmy
        if self.friend or not CFG["amigos"] or not j or self.hidden_fs or quieto(): return
        if time.time() >= self.next_friend and j.sequence_state == "normal" and j.state != "going":
            self.spawn_friend()

    def spawn_friend(self, nome=None):
        j = self.jimmy
        if self.friend or not j or j.sequence_state != "normal": return
        nome = nome or random.choice([n for n in CONVERSAS if n != self.last_friend])
        self.last_friend = nome
        j.state = "idle"
        self.friend = Friend(nome, j, self.friend_done)
        self.friend.show()
        self.next_friend = time.time() + random.uniform(360, 840)

    def friend_done(self, friend):
        if self.friend is friend: self.friend = None

    def toggle_ball(self):
        if not BALL: return
        if BALL.isVisible():
            BALL.put_away()
            if self.goddard: self.goddard.fetch = None
        else:
            BALL.spawn()

    def check_reminders(self):
        if not self.jimmy or self.hidden_fs: return
        now = time.time()
        if not CFG["avisos"] or quieto():
            # Lembretes desligados: zera a contagem para não disparar tudo de uma vez ao religar
            for kind in self.last_rem: self.last_rem[kind] = now
            return
        for kind in ("agua", "pausa", "comer", "exercicio"):
            if not CFG["aviso_" + kind]:
                self.last_rem[kind] = now  # desligado: conta do zero quando ligar
                continue
            if now - self.last_rem[kind] >= CFG["aviso_" + kind + "_min"] * 60:
                if self.jimmy.can_remind():
                    self.jimmy.start_reminder(kind)
                    self.last_rem[kind] = now
                return  # um de cada vez; se ele estiver ocupado, tenta de novo daqui a pouco

    def keep_pets_on_top(self):
        # Ordem importa: sombras e fumaça primeiro, pets por último (ficam na frente)
        for pet in self.pets():
            if pet.shadow: _topmost(pet.shadow)
        if FX: _topmost(FX)
        for pet in self.pets():
            pet.keep_on_top()
        if BALL: _topmost(BALL)
        for m in self.meteoros_vivos: _topmost(m)

    def apply_scale(self):
        # Novo tamanho: limpa os tamanhos calculados e recria os pets
        global ESCALA
        ESCALA = CFG["tamanho"] / 100
        Pet.box_cache.clear()
        self.restart_pets()

    def open_config(self):
        if self.config_window is None:
            self.config_window = Configuracoes(self)
        self.config_window.carregar()
        self.config_window.show()
        self.config_window.raise_()
        self.config_window.activateWindow()

    def quit_app(self):
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())

UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\JimmyNeutronPet"

def desinstalar():
    """Chamado pelo Windows (Aplicativos > Desinstalar) com --desinstalar.
    --teste PASTA: usa PASTA no lugar das pastas reais e não mexe no registro; --sim responde sim a tudo."""
    app = QApplication(sys.argv)
    teste = sys.argv[sys.argv.index("--teste") + 1] if "--teste" in sys.argv else None
    auto = "--sim" in sys.argv
    sim = QMessageBox.StandardButton.Yes

    def pergunta(texto):
        return auto or QMessageBox.question(None, tr("Desinstalar Jimmy Neutron Pet"), tr(texto)) == sim

    if not pergunta("Desinstalar o Jimmy Neutron Pet?"):
        return
    apagar_cfg = pergunta("Apagar também suas configurações e conquistas?")
    # Fecha o pet se estiver aberto (menos este processo e o pai dele, do .exe de arquivo único)
    if not teste:
        subprocess.run(["taskkill", "/F", "/IM", "JimmyNeutronPet.exe",
                        "/FI", f"PID ne {os.getpid()}", "/FI", f"PID ne {os.getppid()}"],
                       capture_output=True, creationflags=0x08000000)
    # Atalhos e pasta gravados pelo instalador
    info = {}
    if teste:
        try:
            with open(os.path.join(teste, "registro.json"), encoding="utf-8") as f:
                info = json.load(f)
        except OSError:
            pass
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as k:
                for nome in ("AtalhoMenu", "AtalhoDesktop", "InstallLocation"):
                    try: info[nome] = winreg.QueryValueEx(k, nome)[0]
                    except OSError: pass
        except OSError:
            pass
    for nome in ("AtalhoMenu", "AtalhoDesktop"):
        if info.get(nome) and os.path.exists(info[nome]):
            os.remove(info[nome])
    if not teste:
        set_autostart(False)
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
        except OSError:
            pass
        if apagar_cfg:
            shutil.rmtree(DATA_DIR, ignore_errors=True)
    if not auto:
        QMessageBox.information(None, tr("Desinstalar"), tr("O Jimmy Neutron Pet foi desinstalado. Até mais! 👋"))
    # Apaga a pasta do programa depois que este processo fechar (só se for a pasta do instalador)
    pasta = os.path.dirname(os.path.abspath(sys.executable))
    esperado = info.get("InstallLocation", "")
    if getattr(sys, "frozen", False) and esperado and os.path.normcase(pasta) == os.path.normcase(esperado):
        subprocess.Popen(f'cmd /c ping 127.0.0.1 -n 4 >nul & rmdir /s /q "{pasta}"',
                         creationflags=0x08000000 | 0x00000008)

if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        try: os.remove(sys.executable + ".old")   # sobra da atualização anterior
        except OSError: pass
    if "--desinstalar" in sys.argv:
        desinstalar()
        sys.exit(0)
    try:
        manager = TrayManager()
        manager.run()
    except Exception as e:
        log_error(e)
        print(f"Erro fatal: {e}")
