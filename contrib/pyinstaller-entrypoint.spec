# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
import platform

def _get_version() -> str:
    try:
        import importlib.metadata
        return importlib.metadata.distribution('ausweiskopie').version
    except ImportError:
        import pkg_resources
        return pkg_resources.get_distribution('ausweiskopie').version

datas = []
datas += collect_data_files('ausweiskopie')


a = Analysis(
    ['pyinstaller-entrypoint.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PIL._tkinter_finder'],
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
    name='ausweiskopie',
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
    icon=["in.varb.Ausweiskopie.ico"]
)
if platform.system() == "Darwin":
    app = BUNDLE (
        exe,
        version = _get_version(),
        name = "Meine Ausweiskopie.app",
        icon = "in.varb.Ausweiskopie.icns",
        bundle_identifier = "in.varb.Ausweiskopie",
        # bundle_display_name = "Ausweiskopie",
        info_plist = {
            "CFBundleDisplayName": "Ausweiskopie",
        }
    )
