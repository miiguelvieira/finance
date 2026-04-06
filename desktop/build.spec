# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para Finance Personal Desktop."""

import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve()  # finance/

block_cipher = None

a = Analysis(
    [str(ROOT / "desktop" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # assets estáticos
        (str(ROOT / "assets"), "assets"),
        # config
        (str(ROOT / "config.yaml"), "."),
        # migrations (Alembic)
        (str(ROOT / "migrations"), "migrations"),
    ],
    hiddenimports=[
        # FastAPI / Uvicorn
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # SQLAlchemy dialects
        "sqlalchemy.dialects.sqlite",
        # Dash internals
        "dash",
        "dash_bootstrap_components",
        "plotly",
        # App modules
        "src.core.config",
        "src.core.database",
        "src.core.models",
        "src.accounts.service",
        "src.accounts.router",
        "src.transactions.service",
        "src.transactions.categorizer",
        "src.transactions.router",
        "src.installments.service",
        "src.installments.router",
        "src.projections.engine",
        "src.projections.router",
        "src.investments.service",
        "src.investments.tax_engine",
        "src.investments.flashcards",
        "src.investments.router",
        "src.pluggy.client",
        "src.pluggy.sync",
        "src.pluggy.router",
        "src.chatbot.intents",
        "src.chatbot.responses",
        "src.chatbot.engine",
        "src.chatbot.router",
        "src.dashboard.theme",
        "src.dashboard.layout",
        "src.dashboard.components.cards",
        "src.dashboard.components.charts",
        "src.dashboard.pages.accounts",
        "src.dashboard.pages.transactions",
        "src.dashboard.pages.investments",
        "src.dashboard.pages.goals",
        "src.dashboard.pages.chatbot",
        "src.api.main",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "notebook", "IPython"],
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
    name="finance",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # sem janela de console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="finance",
)
