"""Assemble the Autodesk App Store .bundle from the dev source tree.

Run:    python packaging/build_bundle.py
Output: dist/ADSK.Courrieu.Extrusions.bundle/  (PackageContents.xml + Contents/)

Bump "version" in Extrusions.manifest per submission (ProductCode is derived
from it; UpgradeCode stays constant forever).
"""
import json
import os
import shutil
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
MODULE = "Extrusions"
with open(os.path.join(ROOT, MODULE + ".manifest"), encoding="utf-8") as _f:
    VERSION = json.load(_f)["version"]

APP_NAME = "Aluminium Extrusions"
AUTHOR = "Alexandre Courrieu"
EMAIL = "alexandre@courri.eu"
URL = "https://github.com/alex-crr/ExtrusionsGenerator"
DESCRIPTION = "Insert 20-series aluminium extrusion profiles at a chosen length."

UPGRADE_CODE = "{c1e7a2d4-5b93-4f08-8a6e-2d9f1b7c4e55}"          # STABLE forever
_NS = uuid.UUID("7b3e9c21-4d6a-4f85-b0c2-e8a1d5f63a97")
PRODUCT_CODE = "{%s}" % uuid.uuid5(_NS, VERSION)                 # per-version
BUNDLE = "ADSK.Courrieu.Extrusions.bundle"

# Runtime files copied into Contents/ (everything else stays out of the bundle).
CONTENTS = [
    "Extrusions.py", "Extrusions.manifest", "config.py",
    "commands/__init__.py", "commands/Extrusion/__init__.py", "commands/Extrusion/entry.py",
    "resources/Extrusion/16x16-normal.png", "resources/Extrusion/32x32-normal.png",
    "resources/Extrusion/64x64-normal.png",
] + ["dxf_profiles/2020/" + f for f in sorted(os.listdir(os.path.join(ROOT, "dxf_profiles", "2020")))]

PACKAGE_CONTENTS = f"""<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage SchemaVersion="1.0" AutodeskProduct="Fusion360"
    Name="{APP_NAME}" Description="{DESCRIPTION}"
    Author="{AUTHOR}" AppVersion="{VERSION}"
    ProductCode="{PRODUCT_CODE}" UpgradeCode="{UPGRADE_CODE}">
  <CompanyDetails Name="{AUTHOR}" Url="{URL}" Email="{EMAIL}"/>
  <Components Description="Fusion 360 Add-in">
    <RuntimeRequirements OS="Win64" Platform="Fusion360" SeriesMin="" SeriesMax=""/>
    <ComponentEntry AppName="{MODULE}" ModuleName="./Contents/{MODULE}.py"
        AppType="addin" Version="{VERSION}" LoadOnFusionStartup="True"/>
  </Components>
</ApplicationPackage>
"""


def build():
    out = os.path.join(DIST, BUNDLE)
    if os.path.exists(out):
        shutil.rmtree(out)
    contents = os.path.join(out, "Contents")
    os.makedirs(contents)
    with open(os.path.join(out, "PackageContents.xml"), "w", encoding="utf-8") as f:
        f.write(PACKAGE_CONTENTS)
    for rel in CONTENTS:
        src = os.path.join(ROOT, *rel.split("/"))
        dst = os.path.join(contents, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    print("built:", out, "| version:", VERSION, "| ProductCode:", PRODUCT_CODE)


if __name__ == "__main__":
    build()
