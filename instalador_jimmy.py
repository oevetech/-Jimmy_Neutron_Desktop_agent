"""Instalador do Jimmy Neutron Pet.

Instala em %LOCALAPPDATA%\\Programs\\Jimmy Neutron Pet (sem precisar de administrador),
cria atalhos e registra em Configurações > Aplicativos para poder desinstalar.

Teste sem mexer no sistema:  "Instalar Jimmy Neutron Pet.exe" --teste PASTA --auto
(instala dentro de PASTA, não grava no registro, não fecha nem abre o pet).
"""
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
import winreg

NOME = "Jimmy Neutron Pet"
EXE = "JimmyNeutronPet.exe"
VERSAO = "1.0"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\JimmyNeutronPet"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
SEM_JANELA = 0x08000000


def recurso(nome):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, nome)
    aqui = os.path.dirname(os.path.abspath(__file__))
    for pasta in (aqui, os.path.join(aqui, "assets"), os.path.join(aqui, "dist")):
        if os.path.exists(os.path.join(pasta, nome)):
            return os.path.join(pasta, nome)
    return os.path.join(aqui, nome)


def pasta_especial(csidl):
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
    return buf.value


def caminhos(teste):
    if teste:
        return {"programa": os.path.join(teste, "Programs", NOME),
                "menu": os.path.join(teste, "MenuIniciar"),
                "desktop": os.path.join(teste, "AreaDeTrabalho")}
    return {"programa": os.path.join(os.environ["LOCALAPPDATA"], "Programs", NOME),
            "menu": pasta_especial(0x02),      # menu Iniciar > Programas
            "desktop": pasta_especial(0x10)}   # Área de Trabalho (funciona com OneDrive)


def criar_atalho(lnk, alvo):
    q = lambda t: t.replace("'", "''")
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(lnk)}');"
          f"$s.TargetPath='{q(alvo)}';$s.WorkingDirectory='{q(os.path.dirname(alvo))}';"
          f"$s.IconLocation='{q(alvo)},0';$s.Description='{NOME}';$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   check=True, capture_output=True, timeout=60, creationflags=SEM_JANELA)


def instalar(desktop=True, iniciar_windows=True, abrir=True, teste=None, progresso=print):
    c = caminhos(teste)
    destino = os.path.join(c["programa"], EXE)
    if not teste:
        progresso("Fechando o pet, se estiver aberto...")
        subprocess.run(["taskkill", "/F", "/IM", EXE], capture_output=True, creationflags=SEM_JANELA)
        time.sleep(1.5)
    progresso("Copiando arquivos...")
    os.makedirs(c["programa"], exist_ok=True)
    for tentativa in range(5):   # o .exe antigo pode demorar um pouco para liberar
        try:
            shutil.copyfile(recurso(EXE), destino)
            break
        except PermissionError:
            if tentativa == 4: raise
            time.sleep(1)
    progresso("Criando atalhos...")
    os.makedirs(c["menu"], exist_ok=True)
    atalho_menu = os.path.join(c["menu"], NOME + ".lnk")
    criar_atalho(atalho_menu, destino)
    atalho_desktop = ""
    if desktop:
        os.makedirs(c["desktop"], exist_ok=True)
        atalho_desktop = os.path.join(c["desktop"], NOME + ".lnk")
        criar_atalho(atalho_desktop, destino)
    registro = {"DisplayName": NOME, "DisplayVersion": VERSAO, "Publisher": "@oevetech",
                "DisplayIcon": destino, "InstallLocation": c["programa"],
                "UninstallString": f'"{destino}" --desinstalar',
                "URLInfoAbout": "https://www.youtube.com/@oevetech",
                "AtalhoMenu": atalho_menu, "AtalhoDesktop": atalho_desktop}
    progresso("Registrando no Windows...")
    if teste:
        with open(os.path.join(teste, "registro.json"), "w", encoding="utf-8") as f:
            json.dump(dict(registro, IniciarComWindows=iniciar_windows), f, indent=2, ensure_ascii=False)
    else:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as k:
            for nome, valor in registro.items():
                winreg.SetValueEx(k, nome, 0, winreg.REG_SZ, valor)
            tamanho = os.path.getsize(destino) // 1024
            winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, tamanho)
            winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if iniciar_windows:
                winreg.SetValueEx(k, "JimmyNeutronPet", 0, winreg.REG_SZ, f'"{destino}"')
            else:
                try: winreg.DeleteValue(k, "JimmyNeutronPet")
                except FileNotFoundError: pass
    if abrir and not teste:
        progresso("Abrindo o pet...")
        subprocess.Popen(["explorer.exe", destino])
    return destino


def janela():
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title(f"Instalar {NOME}")
    root.resizable(False, False)
    try:
        root.iconbitmap(recurso("jimmy.ico"))
    except tk.TclError:
        pass
    root.configure(bg="white")
    topo = tk.Frame(root, bg="white")
    topo.pack(padx=20, pady=(16, 6), fill="x")
    try:
        img = tk.PhotoImage(file=recurso("instalador_jimmy.png"))
        tk.Label(topo, image=img, bg="white").pack(side="left", padx=(0, 14))
        root._img = img
    except tk.TclError:
        pass
    textos = tk.Frame(topo, bg="white")
    textos.pack(side="left", fill="both")
    tk.Label(textos, text=NOME, font=("Segoe UI", 16, "bold"), bg="white").pack(anchor="w")
    tk.Label(textos, text=f"versão {VERSAO} · por @oevetech", font=("Segoe UI", 9), fg="gray", bg="white").pack(anchor="w")
    tk.Label(textos, text="O Jimmy, o Goddard e o foguete\nvão morar na sua barra de tarefas! 🚀",
             font=("Segoe UI", 10), justify="left", bg="white").pack(anchor="w", pady=(8, 0))

    c = caminhos(None)
    tk.Label(root, text=f"Pasta: {c['programa']}", font=("Segoe UI", 8), fg="gray", bg="white",
             wraplength=400, justify="left").pack(padx=20, anchor="w", pady=(8, 4))
    v_desktop, v_win, v_abrir = tk.BooleanVar(value=True), tk.BooleanVar(value=True), tk.BooleanVar(value=True)
    for txt, var in (("Criar atalho na Área de Trabalho", v_desktop),
                     ("Iniciar junto com o Windows", v_win),
                     ("Abrir o pet ao terminar", v_abrir)):
        tk.Checkbutton(root, text=txt, variable=var, bg="white", font=("Segoe UI", 10),
                       activebackground="white").pack(padx=18, anchor="w")
    status = tk.Label(root, text="", font=("Segoe UI", 9), fg="#225", bg="white")
    status.pack(padx=20, pady=(8, 0), anchor="w")
    botoes = tk.Frame(root, bg="white")
    botoes.pack(padx=20, pady=14, fill="x")

    def progresso(t):
        status.config(text=t)
        root.update()

    def fazer():
        b_inst.config(state="disabled")
        b_canc.config(state="disabled")
        try:
            instalar(v_desktop.get(), v_win.get(), v_abrir.get(), progresso=progresso)
        except Exception as e:
            messagebox.showerror("Instalar", f"Não deu para instalar:\n{e}")
            b_inst.config(state="normal")
            b_canc.config(state="normal")
            status.config(text="")
            return
        status.config(text="Pronto! 🎉 Procure \"Jimmy Neutron Pet\" no menu Iniciar.")
        b_inst.pack_forget()
        b_canc.config(text="Fechar", state="normal")

    b_canc = ttk.Button(botoes, text="Cancelar", command=root.destroy)
    b_canc.pack(side="right")
    b_inst = ttk.Button(botoes, text="Instalar", command=fazer)
    b_inst.pack(side="right", padx=(0, 8))
    root.mainloop()


if __name__ == "__main__":
    if "--teste" in sys.argv:
        pasta = sys.argv[sys.argv.index("--teste") + 1]
        print(instalar(teste=pasta, abrir=False))
    else:
        janela()
