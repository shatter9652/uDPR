#!/usr/bin/env python3
"""Stage startup: Assets/Resources/StartupSettings.asset (an exported asset) set up for this project's editor.

- _assetBundleTarget 3 (StreamingAssets bundles) -> 0 (AssetDatabase: the shipped editor path, assets load from the project);
- the initialize methods' assembly "AssetAssistant, Version=0.0.0.0," -> "Assembly-CSharp, Version=1.6.28.12450,": here the
  AssetAssistant code is compiled into Assembly-CSharp; with the shipped name Type.GetType returns null and AssetManager /
  SceneBrowser / SectionCounter never initialise.
BdspWinBuild switches the target to 3 for a player build and restores it afterwards. (Was tools/phase4_settings.py --startup.)

  python -I setup/stages/startup.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import paths  # noqa: E402
import dump_profile  # noqa: E402

REL = os.path.join("Resources", "StartupSettings.asset")


def main():
    p = os.path.join(paths.ASSETS, REL)
    if not os.path.isfile(p):
        sys.exit("no %s - stage merge first" % p)
    old = open(p, encoding="utf-8", newline="").read()
    edition = paths.CFG.get("dump_profile", "BD")
    version = dump_profile.PROFILES[edition]["build_version"]
    if re.findall(r"(?m)^  _buildVersion: ([^\r\n]+)", old) != [version]:
        sys.exit("StartupSettings: expected build version %s for %s" % (version, edition))
    new, n_target = re.subn(r"(?m)^  _assetBundleTarget: \d+$", "  _assetBundleTarget: 0", old)
    n_asm = new.count("AssetAssistant, Version=0.0.0.0,")
    new = new.replace("AssetAssistant, Version=0.0.0.0,", "Assembly-CSharp, Version=1.6.28.12450,")
    if n_target != 1:
        sys.exit("StartupSettings: expected one _assetBundleTarget line, found %d" % n_target)
    if new != old:
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    asm_now = new.count("Assembly-CSharp, Version=1.6.28.12450,")
    print("StartupSettings: _assetBundleTarget 0; assembly names changed %d (now %d on Assembly-CSharp)" % (n_asm, asm_now))
    if "AssetAssistant, Version=0.0.0.0," in new or asm_now != 21:     # 21 = the reference project's count
        sys.exit("StartupSettings: unexpected assembly names after the edit (%d on Assembly-CSharp, reference 21)" % asm_now)


if __name__ == "__main__":
    main()
