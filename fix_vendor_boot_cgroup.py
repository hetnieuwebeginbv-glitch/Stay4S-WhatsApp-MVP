#!/usr/bin/env python3
"""Patch vendor_boot.img: verwijder cgroup_disable=memory + cgroup.memory=nokmem
uit de kernel-commandline-string.

Deze flags in de GrapheneOS-kernel-cmdline breken Android's init (memory-cgroups
zijn vereist voor app-UID-paden). Resultaat: Stay4OS v5 bootloop.

Werkt als volgt:
- Zoekt de cmdline-string (met cgroup_disable=memory)
- Verwijdert "cgroup_disable=memory " en "cgroup.memory=nokmem " (en varianten)
- Schrijft terug op dezelfde plek (zelfde lengte, opgevuld met spaces)
"""
import hashlib
import shutil
import sys

SRC = r"D:\STAY4S-DATA\stay4os-rom\v5\vendor_boot.img"
OUT = r"D:\STAY4S-DATA\stay4os-rom\v5\vendor_boot_fixed.img"

# te verwijderen tokens (variante spellingsfouten in de GrapheneOS-cmdline)
TOKENS = [
    b"cgroup_disable=memory ",
    b"cgroup_disable=memmry ",
    b"cgroup_disable=memroy ",
    b"cgroup.memory=nokmem ",
    b"cgroup.memory=nokmem",
    b"cgroup_disable=pressure ",
]

def patch(path, out):
    with open(path, "rb") as fh:
        d = bytearray(fh.read())
    print(f"in: {path} ({len(d)} bytes)")
    removed = 0
    for tok in TOKENS:
        idx = 0
        while True:
            i = bytes(d).find(tok, idx)
            if i == -1:
                break
            # vervang door evenveel spaces (cmdline is space-gescheiden)
            d[i:i+len(tok)] = b" " * len(tok)
            removed += 1
            idx = i + len(tok)
            print(f"  verwijderd @{i}: {tok.decode()!r}")
    # toon wat overblijft rond cgroup
    chunk = bytes(d)
    for pat in [b"cgroup", b"nokmem", b"bootconfig"]:
        i = chunk.find(pat)
        if i != -1:
            txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk[i-30:i+60])
            print(f"  reste {pat.decode()!r} @{i}: ...{txt}...")
    with open(out, "wb") as fh:
        fh.write(bytes(d))
    print(f"uit: {out} ({len(d)} bytes, {removed} tokens verwijderd)")
    # sha256 beide
    for f in (path, out):
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        print(f"  sha256 {f.split(chr(92))[-1]}: {h[:16]}...")

if __name__ == "__main__":
    patch(SRC, OUT)