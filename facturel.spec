# -*- mode: python ; coding: utf-8 -*-

import os

# Preluăm automat toate fișierele Python locale din proiect (meniu.py, db.py etc.)
local_py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'main.py']
datas_list = [(f, '.') for f in local_py_files]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'meniu',
        'db',
        'tkcalendar',
        'babel.numbers',
        'babel.dates',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'sqlite3',
        'reportlab',  # Generare PDF
        'reportlab.lib',
        'reportlab.platypus',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Facturel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Setat pe False pentru a ascunde fereastra neagră de consolă (GUI mode)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)