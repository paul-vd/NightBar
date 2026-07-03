"""py2app build script.  Build a dev bundle with:  python3 setup.py py2app -A"""
from setuptools import setup

setup(
    app=["nightbar.py"],
    setup_requires=["py2app"],
    options={
        "py2app": {
            "argv_emulation": False,
            "plist": {
                "CFBundleName": "NightBar",
                "CFBundleIdentifier": "com.nightbar.app",
                "LSUIElement": True,  # menu-bar-only, no Dock icon
            },
        }
    },
)
