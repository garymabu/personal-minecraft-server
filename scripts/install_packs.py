#!/usr/bin/env python3
"""Install all .mcaddon/.mcpack files from packs/ into the active world.

Usage: install_packs.py <world-dir>

For each archive in packs/:
  - Unzip into a temp dir.
  - Walk it looking for manifest.json files.
  - Classify each sub-pack by its modules[].type:
      data/script -> behavior pack
      resources   -> resource pack
  - Copy the sub-pack folder into data/behavior_packs/ or data/resource_packs/.
  - Append {pack_id, version} to <world>/world_{behavior,resource}_packs.json
    (skipping any UUID already present).
"""
import json
import os
import shutil
import sys
import tempfile
import zipfile
from glob import glob

if len(sys.argv) != 2:
    sys.exit(__doc__)

world = sys.argv[1]
bp_dir = "data/behavior_packs"
rp_dir = "data/resource_packs"
os.makedirs(bp_dir, exist_ok=True)
os.makedirs(rp_dir, exist_ok=True)

bp_entries = []
rp_entries = []


def classify(manifest):
    for m in manifest.get("modules", []):
        t = m.get("type")
        if t in ("data", "script", "javascript"):
            return "behavior"
        if t == "resources":
            return "resource"
    return None


def install_pack_folder(src):
    manifest_path = os.path.join(src, "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)
    kind = classify(manifest)
    if kind is None:
        print(f"  skip (unknown module type): {src}")
        return
    name = os.path.basename(src.rstrip("/"))
    dest_root = bp_dir if kind == "behavior" else rp_dir
    dest = os.path.join(dest_root, name)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    entry = {
        "pack_id": manifest["header"]["uuid"],
        "version": manifest["header"]["version"],
    }
    (bp_entries if kind == "behavior" else rp_entries).append(entry)
    print(f"  installed {kind} pack: {name}")


def walk_packs(root):
    """Yield directories that contain a manifest.json."""
    for dirpath, _, files in os.walk(root):
        if "manifest.json" in files:
            yield dirpath


def extract_recursive(archive, dest):
    """Extract a zip, then recursively extract any nested .mcpack/.mcaddon/.zip."""
    with zipfile.ZipFile(archive) as z:
        z.extractall(dest)
    for dirpath, _, files in os.walk(dest):
        for name in files:
            if name.lower().endswith((".mcpack", ".mcaddon", ".zip")):
                nested = os.path.join(dirpath, name)
                stem, _ = os.path.splitext(name)
                target = os.path.join(dirpath, stem)
                while os.path.exists(target):
                    target += "_"
                try:
                    extract_recursive(nested, target)
                    os.remove(nested)
                except zipfile.BadZipFile:
                    pass


for archive in sorted(glob("packs/*")):
    if not archive.lower().endswith((".mcaddon", ".mcpack", ".zip")):
        continue
    print(f"processing {archive}")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            extract_recursive(archive, tmp)
        except zipfile.BadZipFile:
            print(f"  not a zip, skipping")
            continue
        for sub in walk_packs(tmp):
            install_pack_folder(sub)


def merge_into(json_path, new_entries):
    if not new_entries:
        return
    arr = []
    if os.path.isfile(json_path):
        with open(json_path) as f:
            arr = json.load(f)
    by_id = {e["pack_id"]: e for e in arr}
    added = updated = 0
    for e in new_entries:
        existing = by_id.get(e["pack_id"])
        if existing is None:
            arr.append(e)
            by_id[e["pack_id"]] = e
            added += 1
        elif existing.get("version") != e["version"]:
            existing["version"] = e["version"]
            updated += 1
    with open(json_path, "w") as f:
        json.dump(arr, f, indent=4)
    print(f"updated {json_path} (+{added} new, {updated} version bump)")


merge_into(os.path.join(world, "world_behavior_packs.json"), bp_entries)
merge_into(os.path.join(world, "world_resource_packs.json"), rp_entries)
