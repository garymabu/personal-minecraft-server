#!/usr/bin/env python3
"""Remove a Bedrock add-on by folder-name substring.

Usage: uninstall_pack.py <needle> <world-dir>

Deletes matching folders from data/{behavior,resource}_packs, removes their
pack_id entries from <world-dir>/world_{behavior,resource}_packs.json, and
deletes matching .mcaddon/.mcpack files from packs/.
"""
import json
import os
import shutil
import sys
from glob import glob

if len(sys.argv) != 3:
    sys.exit(__doc__)

needle = sys.argv[1].lower()
world = sys.argv[2]
uuids = set()

for root in ("data/behavior_packs", "data/resource_packs"):
    if not os.path.isdir(root):
        continue
    for entry in os.listdir(root):
        if needle not in entry.lower():
            continue
        path = os.path.join(root, entry)
        manifest = os.path.join(path, "manifest.json")
        if os.path.isfile(manifest):
            with open(manifest) as f:
                uuids.add(json.load(f)["header"]["uuid"])
        print(f"rm -rf {path}")
        shutil.rmtree(path)

for name in ("world_behavior_packs.json", "world_resource_packs.json"):
    path = os.path.join(world, name)
    if not os.path.isfile(path):
        continue
    with open(path) as f:
        arr = json.load(f)
    kept = [e for e in arr if e.get("pack_id") not in uuids]
    if kept != arr:
        with open(path, "w") as f:
            json.dump(kept, f, indent=4)
        print(f"updated {path} ({len(arr) - len(kept)} entry/entries removed)")

for src in glob("packs/*"):
    base = os.path.basename(src).lower()
    if needle in base and (base.endswith(".mcaddon") or base.endswith(".mcpack")):
        print(f"rm {src}")
        os.remove(src)

if not uuids:
    print(f"warning: no pack folders matched '{sys.argv[1]}'")
