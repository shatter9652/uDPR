#!/usr/bin/env python3
"""BDSP PC rebuild - automated project setup: turns the user's own game dump into this Unity project's assets.

  python setup/setup.py --dump <folder with exefs\\ and romfs\\> [--unity <Unity.exe 2019.4.27f1>] [--wwise <project with the
                        Launcher's Wwise integration>] [--assetripper <AssetRipper.GUI.Free.exe>] [--work <folder>]
                        [--from STAGE] [--only STAGE] [--until STAGE] [--keep-backups] [--list]

Each stage runs as its own process with a log in <work>/logs/<stage>.log; <work>/state.json records the finished stages, so
running the command again resumes after the last one that finished (--from / --only re-run on purpose). Settings given once are
kept in <work>/config.json.
"""
import argparse
import datetime
import importlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import paths  # noqa: E402
import dump_profile  # noqa: E402

PY = [sys.executable, "-I"]
STAGES_DIR = os.path.join(paths.SETUP, "stages")


def stage_cmd(script, *args):
    return PY + [os.path.join(STAGES_DIR, script)] + [str(x) for x in args]


def unity_cmd(method, marker=None, *extra):
    return PY + [os.path.join(paths.SETUP, "lib", "unity.py"), "--method", method] + (["--marker", marker] if marker else []) \
        + list(extra)


def build_stages(planned_work=None):
    """(name, what it does, [command, ...] or None while not ported yet) - built after the config is written, so the paths in
    the commands are the configured ones."""
    W = paths.work if planned_work is None else lambda *parts: os.path.join(planned_work, *parts)
    AA, P = paths.AA, paths.PROJECT
    return [
        ("check", "preflight: dump, Unity, Wwise, tools, disk, RAM", [stage_cmd("check.py")]),
        ("export", "AssetRipper exports the dump into <work>/export", [stage_cmd("ar_export.py")]),
        ("fix_arrays", "repair the negative values the free AssetRipper export damages in hex arrays", [stage_cmd("fix_arrays.py")]),
        ("normalise", "the export's random asset GUIDs -> this project's GUIDs; package/Wwise/DOTween script references",
         [stage_cmd("normalise_guids.py")]),
        ("merge", "move the exported asset folders into Assets/ (sound banks Switch -> Windows)", [stage_cmd("merge.py")]),
        ("wwise", "copy the Wwise integration files in; AkInitializer.LateUpdate / AkGameObj.SetPosition public",
         [stage_cmd("wwise.py")]),
        ("startup", "StartupSettings: load assets from the project in the editor", [stage_cmd("startup.py")]),
        ("shaders", "install the recovered shaders over the exported placeholders", [stage_cmd("shaders.py")]),
        ("containers", "scan the shipped bundles' container tables; map them to project files", [
            stage_cmd("bundle_containers.py", "scan", AA, "--out", W("atlas", "bundle_containers.json")),
            stage_cmd("bundle_containers.py", "map", "--containers", W("atlas", "bundle_containers.json"), "--project", P,
                      "--out", W("atlas", "bundle_map.json"), "--report", W("atlas", "bundle_map_report.txt"))]),
        ("atlas_spec", "SpriteAtlas rebuild spec from the shipped atlases", [
            stage_cmd("spriteatlas_spec.py", "--aa", AA, "--containers", W("atlas", "bundle_containers.json"),
                      "--map", W("atlas", "bundle_map.json"), "--project", P, "--out", W("atlas", "spriteatlas_spec.json"),
                      "--report", W("atlas", "spriteatlas_report.txt"))]),
        ("sprite_bake", "bake the atlas binding into packed sprites", [
            stage_cmd("sprite_bake.py", "--spec", W("atlas", "spriteatlas_spec.json"), "--project", P,
                      "--backup", W("atlas", "sprite_bake_backup"), "--report", W("atlas", "sprite_bake_report.txt"),
                      "--apply")]),
        ("atlases", "first Unity import + build the sprite atlases (Unity editor; the first import takes long)", [
            unity_cmd("BdspAtlas.BuildAll", "BDSP_ATLAS_BUILD_DONE"),
            stage_cmd("pin_atlases.py")]),
        ("placeholders", "point the exported SpriteAtlas placeholders at the rebuilt atlases; write bundle_map.tsv", [
            stage_cmd("placeholders.py"),
            stage_cmd("bundle_containers.py", "map", "--containers", W("atlas", "bundle_containers.json"), "--project", P,
                      "--out", W("atlas", "bundle_map.json"), "--report", W("atlas", "bundle_map_report.txt"),
                      "--tsv", paths.TSV)]),
        ("sprite_restore", "restore the shipped sprite geometry", [
            stage_cmd("sprite_shipped_index.py"),
            stage_cmd("sprite_restore_shipped.py", "--apply")]),
        ("d7", "every texture holds the shipped texels (incl. the editor template + verify steps)", [stage_cmd("d7.py")]),
        ("untag", "empty the runtime atlas tags of packed sprites (needed for Windows bundles)", [
            stage_cmd("sprite_untag.py", "--apply", "--project", P, "--backup", W("build", "sprite_untag_backup"))]),
        ("verify", "reimport, audits, play smoke (Unity editor)", [stage_cmd("verify.py")]),
        ("build", "OPTIONAL (--build): standalone Windows game in Builds/ (bundles + IL2CPP player)", [stage_cmd("build.py")]),
    ]


OPTIONAL = {"build"}       # runs only when asked for (--build / setup.cmd -Build) - and then every time: a rebuild

# Stage versions. Bump a stage's number when a change to it must reach setups that already ran it: the next setup.cmd runs that
# stage again on the finished project (with BDSP_STAGE_FRESH=1, so the stage starts its own sub-steps over and may update what it
# installed earlier), then `verify`. Only stages in RERUNNABLE are known to be safe on a finished project; a newer version of any
# other stage stops with "this update needs a fresh setup". A NEW stage needs no version: setups that never ran it run it - so a
# new stage must also work on a finished project (see fix_arrays). Stages missing here are version 1.
VERSIONS = {}
RERUNNABLE = {"fix_arrays", "wwise", "startup", "shaders", "verify"}


NAMES = ["check", "export", "fix_arrays", "normalise", "merge", "wwise", "startup", "shaders", "containers", "atlas_spec", "sprite_bake",
         "atlases", "placeholders", "sprite_restore", "d7", "untag", "verify", "build"]


def log(msg):
    line = "%s %s" % (datetime.datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(paths.work("logs", "setup.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for k in ("dump", "unity", "wwise", "assetripper", "work"):
        ap.add_argument("--" + k)
    ap.add_argument("--from", dest="start", choices=NAMES)
    ap.add_argument("--only", choices=NAMES)
    ap.add_argument("--until", choices=NAMES)
    ap.add_argument("--keep-backups", action="store_true")
    ap.add_argument("--build", action="store_true", help="also run the optional build stage (standalone Windows game)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--plan", action="store_true", help="print what a run would do, run nothing")
    a = ap.parse_args()
    global paths
    if a.list:
        for n, what, cmds in build_stages(paths.WORK):
            print("%-15s %s%s" % (n, what, "" if cmds else "   [not ported yet]"))
        return
    cfg = dict(paths.CFG)
    for k in ("dump", "unity", "wwise", "assetripper", "work"):
        v = getattr(a, k)
        if v:
            cfg[k] = os.path.abspath(v)
    if a.keep_backups:
        cfg["keep_backups"] = True
    work = cfg.get("work") or paths.DEFAULT_WORK
    state_path = os.path.join(work, "state.json")
    state = json.load(open(state_path, encoding="utf-8")) if os.path.exists(state_path) else {}
    if not a.plan:
        try:
            edition = dump_profile.identify(cfg.get("dump"))
        except (OSError, ValueError) as e:
            sys.exit("dump: %s" % e)
        previous = cfg.get("dump_profile")
        if previous is None and os.path.isfile(os.path.join(paths.ASSETS, "Resources", "StartupSettings.asset")):
            previous = "BD"  # A project prepared before profiles could only have used Brilliant Diamond.
        if previous is not None and previous != edition:
            sys.exit("this project is set up for %s; use a fresh clone for %s" % (previous, edition))
        work_edition = state.get("dump_profile")
        if work_edition is None and (state or os.path.isdir(os.path.join(work, "export"))):
            same_work = os.path.normcase(os.path.abspath(work)) == os.path.normcase(paths.WORK)
            work_edition = previous if previous is not None and same_work else "BD"
        if work_edition is not None and work_edition != edition:
            sys.exit("the work folder holds %s setup data; use an empty work folder for %s" % (work_edition, edition))
        cfg["dump_profile"] = edition
        os.makedirs(os.path.dirname(paths.CONFIG_PATH), exist_ok=True)
        with open(paths.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=1)
        if state.get("dump_profile") != edition:
            state["dump_profile"] = edition
            os.makedirs(work, exist_ok=True)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=1)
        os.environ["BDSP_SETUP_CONFIG"] = paths.CONFIG_PATH
        paths = importlib.reload(paths)
    stages = build_stages(work if a.plan else None)
    assert [s[0] for s in stages] == NAMES
    names = NAMES
    if a.only:
        names = [a.only]
    else:
        if a.start:
            names = names[names.index(a.start):]
        if a.until:
            names = names[:names.index(a.until) + 1]
    say = print if a.plan else log
    ran = False                                  # a non-optional stage ran -> verify runs again at the end
    for n, what, cmds in stages:
        if n not in names:
            continue
        if n in OPTIONAL and not (a.build or a.only == n or a.start == n):
            say("skip %-14s (optional - add --build / setup.cmd -Build)" % n)
            continue
        st = state.get(n, {})
        want_v, have_v = VERSIONS.get(n, 1), st.get("version", 1)
        fresh = False
        if st.get("done") and not (a.only or a.start) and n not in OPTIONAL:
            if have_v < want_v:
                if n not in RERUNNABLE:
                    say("STOP %-14s version %d -> %d, and this stage cannot run again on a finished project" % (n, have_v, want_v))
                    sys.exit("this update changes the '%s' stage, which needs a fresh setup: run setup.cmd in a new clone of the "
                             "repository (your current project is left as it is)" % n)
                say("UPDATE %-12s version %d -> %d: runs again on the finished project" % (n, have_v, want_v))
                fresh = True
            elif n == "verify" and ran:
                say("AGAIN %-13s (stages ran above)" % n)
            else:
                say("skip %-14s (done %s)" % (n, st["done"]))
                continue
        if cmds is None:
            sys.exit("stage '%s' is not ported yet - stopping before it" % n)
        if a.plan:
            say("RUN  %-14s %s" % (n, what))
            if n not in OPTIONAL:
                ran = True
            continue
        log("STAGE %-13s %s" % (n, what))
        env = dict(os.environ, BDSP_STAGE_FRESH="1") if fresh else None
        for cmd in cmds:
            with open(paths.work("logs", n + ".log"), "a", encoding="utf-8") as lf:
                lf.write("\n=== %s %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), " ".join(cmd)))
                lf.flush()
                p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding="utf-8", errors="replace", env=env)
                for line in p.stdout:
                    lf.write(line)
                    print("    " + line.rstrip(), flush=True)
                rc = p.wait()
            if rc != 0:
                log("FAILED %s (exit %d) - see %s; fix and run again to resume here" % (n, rc,
                                                                                          paths.work("logs", n + ".log")))
                sys.exit(rc)
        state[n] = {"done": datetime.datetime.now().isoformat(timespec="seconds"), "version": VERSIONS.get(n, 1)}
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1)
        if n not in OPTIONAL:
            ran = True
    if a.plan:
        return
    log("finished: %s" % ", ".join(n for n in names if state.get(n, {}).get("done")))


if __name__ == "__main__":
    main()
