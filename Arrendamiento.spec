# -*- mode: python ; coding: utf-8 -*-
# Empaqueta la app como Arrendamiento.app (macOS).
# Construir con: pyinstaller Arrendamiento.spec --clean
#
# app/viewer3d/ (html/js/three.js vendorizado) se empaqueta como recurso de
# solo lectura; los datos del usuario (BD, documentos, modelos 3D) NO se
# empaquetan — se crean en ~/Library/Application Support/Arrendamiento en
# tiempo de ejecución (ver app/paths.py).

datas = [
    ("app/viewer3d/index.html", "app/viewer3d"),
    ("app/viewer3d/app.js", "app/viewer3d"),
    ("app/viewer3d/vendor", "app/viewer3d/vendor"),
]

a = Analysis(
    ["app/main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name="Arrendamiento",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Arrendamiento",
)

app = BUNDLE(
    coll,
    name="Arrendamiento.app",
    icon="assets/icon/AppIcon.icns",
    bundle_identifier="com.arrendamiento.app",
    info_plist={
        "CFBundleName": "Arrendamiento",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
    },
)
