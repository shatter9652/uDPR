#!/usr/bin/env python3
"""Stage normalise: rewrite the fresh AssetRipper export to this project's GUIDs, in place (author D-S1).

AssetRipper gives every exported asset a RANDOM GUID on each run, so every export differs. setup/data/guid_table.tsv.gz holds,
for every asset path of a free-AssetRipper 1.3.14 export of BDSP v1.3.0, the GUID this project uses for it. This stage:
  1. writes our GUID into every asset .meta (the rest of the .meta stays as exported);
  2. writes the DefaultImporter .meta Unity itself would write (with our GUID) for assets the export leaves without one
     (StreamingAssets files);
  3. rewrites the GUID references inside every YAML asset (files starting with "%YAML"):
       - asset GUIDs: export GUID -> our GUID (from steps 1-2);
       - script GUIDs listed in setup/data/script_refs.tsv (classes taken from Unity's packages, the Wwise integration or
         DOTween.dll): export class GUID -> the real one; DOTweenSettings also gets the DLL's fileID. Every other script
         GUID is class-derived and already equals this project's .cs.meta GUID.
Refuses if the export's asset paths do not match the table (different game or AssetRipper version). Disk use stays flat.

  python -I setup/stages/normalise_guids.py [--export <ExportedProject/Assets>] [--dry]
"""
import argparse
import gzip
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import paths  # noqa: E402

SKIP_TOP = {"Scripts"}                       # the export's decompiled scripts are never used (scripts come from git)
META_GUID = re.compile(rb"^guid: ([0-9a-f]{32})", re.M)
REF = re.compile(rb"fileID: (-?\d+), guid: ([0-9a-f]{32})")
DEFAULT_META = ("fileFormatVersion: 2\nguid: %s\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n"
                "  assetBundleVariant: \n")
DONE = "NORMALISED"
DIAMOND_MOVIES = "StreamingAssets/Movie/dia/"
PEARL_MOVIES = "StreamingAssets/Movie/pea/"


def load_table():
    table = {}
    pearl = paths.CFG.get("dump_profile") == "SP"
    with gzip.open(os.path.join(paths.SETUP_DATA, "guid_table.tsv.gz"), "rt", encoding="utf-8") as f:
        next(f)
        for line in f:
            p, g = line.rstrip("\n").split("\t")[:2]
            if pearl and p.startswith(DIAMOND_MOVIES):
                # The same opening and ending slots have edition-specific paths in the two exports.
                p = PEARL_MOVIES + p[len(DIAMOND_MOVIES):].replace("/movie_dia_", "/movie_pea_", 1)
            table[p] = g
    scripts = {}
    with open(os.path.join(paths.SETUP_DATA, "script_refs.tsv"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("export_guid"):
                continue
            exp, tgt, fid, _cls = line.rstrip("\n").split("\t")
            scripts[exp.encode()] = (tgt.encode(), fid.encode() if fid else None)
    return table, scripts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=paths.EXPORT_ASSETS)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    root = a.export
    marker = os.path.join(os.path.dirname(os.path.dirname(root)), DONE)
    if os.path.exists(marker):
        print("already normalised (%s)" % marker)
        return
    table, scripts = load_table()
    assets = []
    for dp, dn, fn in os.walk(root):
        rel_dp = os.path.relpath(dp, root).replace("\\", "/")
        if rel_dp.split("/")[0] in SKIP_TOP:
            dn[:] = []
            continue
        for f in fn:
            if not f.endswith(".meta"):
                assets.append(f if rel_dp == "." else rel_dp + "/" + f)
    present = set(assets)
    not_in_table = sorted(p for p in assets if p not in table)
    missing = sorted(set(table) - present)
    print("export assets %d, table rows %d, not in table %d, table rows missing in the export %d" % (
        len(assets), len(table), len(not_in_table), len(missing)))
    if not_in_table or missing:
        for p in (not_in_table[:10] + missing[:10]):
            print("  mismatch: " + p)
        sys.exit("the export does not match setup/data/guid_table.tsv.gz - wrong game version or AssetRipper version?")
    remap = {}
    rewritten = written = 0
    for p in assets:
        ours = table[p]
        mp = os.path.join(root, p + ".meta")
        if os.path.exists(mp):
            data = open(mp, "rb").read()
            m = META_GUID.search(data)
            if not m:
                sys.exit("no guid line in " + mp)
            theirs = m.group(1)
            if theirs.decode() != ours:
                remap[theirs] = ours.encode()
                if not a.dry:
                    open(mp, "wb").write(data[:m.start(1)] + ours.encode() + data[m.end(1):])
                rewritten += 1
        else:
            if not a.dry:
                with open(mp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(DEFAULT_META % ours)
            written += 1
    print("metas: %d GUIDs rewritten, %d written new" % (rewritten, written))
    files = refs = srefs = 0
    for i, p in enumerate(assets):
        fp = os.path.join(root, p)
        with open(fp, "rb") as f:
            if f.read(5) != b"%YAML":
                continue
        data = open(fp, "rb").read()
        n = [0, 0]

        def sub(m):
            g = m.group(2)
            s = scripts.get(g)
            if s:
                n[1] += 1
                fid = s[1] if (s[1] and m.group(1) == b"11500000") else m.group(1)
                return b"fileID: " + fid + b", guid: " + s[0]
            new = remap.get(g)
            if new is None:
                return m.group(0)
            n[0] += 1
            return b"fileID: " + m.group(1) + b", guid: " + new
        out = REF.sub(sub, data)
        if n[0] or n[1]:
            files += 1
            refs += n[0]
            srefs += n[1]
            if not a.dry:
                open(fp, "wb").write(out)
        if i % 25000 == 0:
            print("  scanned %d / %d" % (i, len(assets)), flush=True)
    print("references rewritten: %d asset + %d script in %d files%s" % (refs, srefs, files, " (DRY RUN)" if a.dry else ""))
    if not a.dry:
        with open(marker, "w", encoding="utf-8") as f:
            f.write("metas %d rewritten %d written; refs %d asset %d script in %d files\n" % (rewritten, written, refs, srefs,
                                                                                            files))


if __name__ == "__main__":
    main()
