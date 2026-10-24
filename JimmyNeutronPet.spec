# -*- mode: python ; coding: utf-8 -*-
# Gera dist/JimmyNeutronPet.exe com as animações e os sons embutidos.
# Uso: python -m PyInstaller --noconfirm JimmyNeutronPet.spec   (ou rode build.ps1)


a = Analysis(
    ['jimmy_pet.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/anim', 'recursos/anim'), ('assets/sons', 'recursos/sons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JimmyNeutronPet',
    icon='assets/jimmy.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
