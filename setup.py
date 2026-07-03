"""py2app build script.  Build with:  python3 setup.py py2app  (or `make build`)"""
import os

from setuptools import setup

py2app_opts = {
    "argv_emulation": False,
    "plist": {
        "CFBundleName": "NightBar",
        "CFBundleIdentifier": "com.nightbar.app",
        "LSUIElement": True,  # menu-bar-only, no Dock icon
    },
}

# Use the app icon if it's been built (assets/NightBar.icns is committed).
_icns = os.path.join("assets", "NightBar.icns")
if os.path.exists(_icns):
    py2app_opts["iconfile"] = _icns

setup(
    app=["nightbar.py"],
    setup_requires=["py2app"],
    options={"py2app": py2app_opts},
)
