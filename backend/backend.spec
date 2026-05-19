# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

# Collect mediapipe data files (models, graphs, etc.)
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

mediapipe_datas = collect_data_files('mediapipe')
cv2_datas = collect_data_files('cv2')

a = Analysis(
    ['backend_runner.py'],
    pathex=['.'],
    binaries=collect_dynamic_libs('cv2') + collect_dynamic_libs('mediapipe'),
    datas=[
        ('model/model.keras', 'model'),
        ('model/labels.json', 'model'),
        ('utils/__init__.py', 'utils'),
        ('utils/landmarks.py', 'utils'),
        ('utils/preprocess.py', 'utils'),
        ('utils/dataset.py', 'utils'),
        ('main.py', '.'),
        *mediapipe_datas,
        *cv2_datas,
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'starlette',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'tensorflow',
        'mediapipe',
        'cv2',
        'numpy',
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'h11',
        'anyio',
        'anyio.abc',
        'anyio._backends._asyncio',
        'asyncio',
        'utils.landmarks',
        'utils.preprocess',
        'model.predict',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL', 'IPython', 'jupyter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='backend',
)
