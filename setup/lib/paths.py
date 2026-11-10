"""Paths for every setup stage, from one config file.

The repository root (= the Unity project) is found from this file's location. Everything else comes from the setup config:
  <project>/SetupWork/config.json   (written by setup.py; another file can be named in the environment variable
                                     BDSP_SETUP_CONFIG)
Keys:
  dump        folder holding the user's game dump: exefs/main + romfs/Data
  dump_profile  BD or SP, determined from the dump's fingerprints by setup.py
  unity       Unity.exe of 2019.4.27f1
  work        folder for intermediate files (default <project>/SetupWork - keep it on the project's drive: the export is MOVED
              into Assets/, never copied)
  assetripper AssetRipper.GUI.Free.exe 1.3.14
  wwise       a Unity project into which the Audiokinetic Launcher integrated Wwise 2019.2.5 (its Assets/Wwise is copied in)
  keep_backups  true = stages keep their before-images under work/ (developer runs); default false
"""
import json
import os

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(PROJECT, "Assets")
SETUP = os.path.join(PROJECT, "setup")
SETUP_DATA = os.path.join(SETUP, "data")
DEFAULT_WORK = os.path.join(PROJECT, "SetupWork")
CONFIG_PATH = os.environ.get("BDSP_SETUP_CONFIG") or os.path.join(DEFAULT_WORK, "config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:      # -sig: Windows PowerShell 5.1 writes UTF-8 with a BOM
            return json.load(f)
    return {}


CFG = load_config()
WORK = os.path.abspath(CFG.get("work") or DEFAULT_WORK)
DUMP = os.path.abspath(CFG["dump"]) if CFG.get("dump") else None
ROMFS = os.path.join(DUMP, "romfs") if DUMP else None
DATA = os.path.join(ROMFS, "Data") if ROMFS else None                       # the game's Unity data folder (romfs/Data)
AA = os.path.join(DATA, "StreamingAssets", "AssetAssistant") if DATA else None
EXPORT = os.path.join(WORK, "export")                                      # AssetRipper output (ExportedProject/Assets inside)
EXPORT_ASSETS = os.path.join(EXPORT, "ExportedProject", "Assets")
BIN = os.path.join(WORK, "bin")                                            # downloaded / built helper programs
KEEP_BACKUPS = bool(CFG.get("keep_backups", False))
TSV = os.path.join(ASSETS, "Editor", "EditorAssetAssistant", "bundle_map.tsv")


def need(value, what):
    if not value:
        raise SystemExit("setup config: '%s' is not set (%s)" % (what, CONFIG_PATH))
    return value


def work(*parts):
    """A path under the work folder; its parent folder is created."""
    p = os.path.join(WORK, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def data_path():
    return need(DATA, "dump")
