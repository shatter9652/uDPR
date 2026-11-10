# uDPR

**Pokémon Brilliant Diamond and Shining Pearl as a Unity project** that rebuilds the game from **your own dump** and builds a standalone game from it. The game logic runs as compiled C#, not under emulation.

> **Made with AI.** This project was made almost entirely with AI - Claude (Anthropic), through Claude Code - directed, tested and
> reviewed by a human.

**No game files are included.** You need your own legally obtained copy of Brilliant Diamond or Shining Pearl, updated to v1.3.0 and
dumped from your own Switch. How to dump it is not covered here.

## Status

**Beta.** The game boots, plays and saves, both in the Unity editor and as a standalone Windows build. Large parts of the game have
not been played through on PC yet, so expect bugs - please report them (see [Contributing](#contributing)).

## Features

- **Native Windows game** - the game's C# compiled by Unity (IL2CPP), with the shipped asset bundles rebuilt for Windows.
- **PC options** - the in-game Options menu starts with nine PC rows: **Display Mode** (Windowed / Borderless Window / Full
  Screen), **Resolution**, **Frame Rate** (30 FPS = the original pace, up to Unlimited), **V-Sync**, **Fast-Forward Speed**
  (2x-8x), **Fast-Forward Key** (Hold / Toggle), **Button Layout** (Switch positions / Xbox labels), **Keyboard Keys** and
  **Controller Buttons**.
- **Keyboard and gamepad** - full keyboard controls and any XInput gamepad, both rebindable in the Options, plus an Xbox-letter
  button layout.
- **Fast-forward** - press Tab (or the gamepad's left stick) to run the game 2x-8x faster; contests, Poffin cooking and movies stay
  at normal speed. See [Fast-forward](#fast-forward).
- **Shipped save format** - saves are written in the game's own format.
- **A real Unity project** - open it in the Unity editor and press Play; every scene, prefab and script is there to study, mod, or
  port to other platforms Unity supports.

## What you need

1. **Windows 10 or 11** (64-bit) on an **SSD**.
2. **Unity 2019.4.27f1** through [Unity Hub](https://unity.com/download) (a free Personal licence is enough). The setup opens Unity
   Hub on that exact version if it is missing.
3. **Wwise 2019.2.5.7349** through the [Audiokinetic Launcher](https://www.audiokinetic.com/download/) (free account): the SDK (C++)
   with Microsoft > Windows (Visual Studio 2019). The setup tells you the one Launcher step it needs.
4. **Your dump of Brilliant Diamond or Shining Pearl v1.3.0** (the base game with the v1.3.0 update applied): a folder holding
   `exefs\` (with `main`) and `romfs\` (with `Data\`). The setup identifies the edition from the dump's files.
5. **About 60 GB free** on the drive that holds this folder (about 45 GB stays in use afterwards; building the standalone game
   adds about 10 GB).
6. **RAM: 32 GB recommended.** The asset export needs about 21 GB of memory and Unity's first import up to about 16 GB. With 16 GB of
   RAM, Windows makes up the difference from its page file: slower, and it needs the page file to be system-managed (the default)
   with about 15 GB free on the system drive. 16 GB has not been tested on a real 16 GB PC yet.

To build the standalone game you also need Unity's **Windows Build Support (IL2CPP)** module and **Visual Studio 2022** (Build Tools or
Community) with **Desktop development with C++** - see [Building the Windows game](#building-the-windows-game).

## Setup

1. Get this repository: `git clone https://github.com/pkdec/uDPR.git` (or **Code > Download ZIP** and unpack it).
2. Run **`setup.cmd`** in its folder.

The setup:

- asks for your dump folder;
- downloads its own tools into `SetupWork\`, each checked against a pinned checksum: a portable Python and AssetRipper 1.3.14.
  Nothing is installed system-wide;
- asks you to integrate Wwise into a folder it creates (one Audiokinetic Launcher step - the setup prints exactly what to click);
- then runs unattended: it exports the game's assets from your dump, matches them to this project, rebuilds the sprite atlases,
  restores the shipped textures, and checks the result (an import report, an audit of the project, and a short play test).

It takes about **3 hours** on a high-end PC, longer on slower ones. Unity windows open and close by themselves - do not close them.

If anything stops it, fix the reported problem and run `setup.cmd` again: it continues where it stopped. Logs: `SetupWork\logs\`.
The setup window's own text is kept in `SetupWork\logs\bootstrap.log`. Use `setup.cmd -Dump <folder>` to relocate a dump of the
same edition. Use a separate checkout for each edition so their generated assets and build caches stay separate.

## Updating

When the repository gets new features or fixes:

1. **`git pull`** (or download the ZIP again and copy it over your folder - keep `SetupWork\` and `Builds\`).
2. **`setup.cmd`** - it runs only what the update needs: new setup steps, and steps that changed in a way your project must get.
   When nothing is needed it says so in a few seconds. If an update ever needs a completely fresh setup, it tells you and changes
   nothing.
3. **Open the project in Unity** - it recompiles the new code on its own.
4. **`setup.cmd -Build`** if you play the standalone game - every `-Build` builds it again: only the asset bundles that changed are
   rebuilt, and the new game goes into a new `Builds\win64_<time>` folder. Older build folders keep working; delete the ones you no
   longer need.

`setup\setup.py --plan` (run it with the setup's own Python: `SetupWork\bin\python\tools\python.exe -I setup\setup.py --plan`) prints
what a run would do without doing it.

## Playing in the editor

Add this folder as a project in Unity Hub (Unity 2019.4.27f1), open `Assets/Scenes/level0.unity` and press Play. In the editor the
game loads its assets straight from the project.

## Building the Windows game

Install Unity's **Windows Build Support (IL2CPP)** module (Unity Hub > Installs > 2019.4.27f1 > Add modules) and **Visual Studio 2022**
(Build Tools or Community) with **Desktop development with C++**, then run **`setup.cmd -Build`**. After a finished setup it only runs
the build: the asset-bundle plan, all 13,651 asset bundles (about 40 minutes and 7 GB the first time; later builds redo only the
bundles that changed) and the IL2CPP player.

The game lands in `Builds\win64_<time>\Dpr.exe`; build reports in `SetupWork\build\reports\`. In the editor the same steps are in
the menu **BDSP > Windows Build**.

**Your build contains the game's assets - do not share it.**

## Controls

| Switch | Keyboard | XInput gamepad |
|---|---|---|
| A / B / X / Y | Z / X / C / V | B / A / Y / X (by position, as on a Switch) |
| L / R | E / U | LB / RB |
| ZL / ZR | Q / O | LT / RT |
| + / − | `=` / `-` | Start / Back |
| D-pad | arrow keys | D-pad |
| Left stick / right stick | WASD / IJKL | left stick / right stick |
| Right stick press | H | RS |
| Fast-forward (PC) | Tab | LS (left stick press - the game never uses it) |

These are the defaults. Change them in **Options > Keyboard Keys / Controller Buttons**: pick an action, press A, then press the
new key or button (Esc or 5 seconds cancels). A key that already belongs to another action swaps with it, and the menu buttons
(A, B, X, Y, +, D-pad) always keep a key, so you cannot lock yourself out. **Options > Button Layout > Xbox Labels** puts the
gamepad's A / B / X / Y on the Switch buttons with the same letter. The bindings are saved in `pc_settings.ini` (`key.*` /
`pad.*` lines; delete them to get the defaults back).

### Fast-forward

- Press **Tab** (keyboard) or the **left stick** (gamepad) to start fast-forward, and again to stop. With **Options >
  Fast-Forward Key > Hold** it runs only while the key is held. **Options > Fast-Forward Speed** picks 2x, 3x, 4x, 6x or 8x.
- `>> 4x` shows in the top-right corner while it runs.
- Fast-forward needs about 30 FPS per 1x: 4x needs 120 FPS, 8x needs 240. A PC that can't draw that many frames gets less, and the
  corner shows the speed it reaches (for example `>> 3.2x`).
- With V-Sync on, V-Sync is switched off while fast-forwarding when the monitor is too slow for the speed (a 60 Hz monitor above
  2x), so you may see tearing only while it runs.
- Contests, Poffin cooking and movies always run at normal speed (they follow the music, your stick speed, or the video). Music
  and sound effects keep their normal speed too.

## PC options

The in-game **Options** menu starts with nine rows the Switch game doesn't have. They are saved in `pc_settings.ini`, not in
your save file.

| Row | Choices | Default |
|---|---|---|
| Display Mode | Windowed / Borderless Window / Full Screen | Borderless Window |
| Resolution | your monitor's sizes from 1280 x 720 up | your desktop size |
| Frame Rate | 30 FPS (the original pace), 60 ... 240, your monitor's rate, Unlimited | Unlimited |
| V-Sync | On / Off | On |
| Fast-Forward Speed | 2x / 3x / 4x / 6x / 8x | 4x |
| Fast-Forward Key | Hold / Toggle | Toggle |
| Button Layout | Switch Positions / Xbox Labels | Switch Positions |
| Keyboard Keys | press A to change the keyboard keys | Default |
| Controller Buttons | press A to change the gamepad buttons | Default |

Changes take effect when you answer **Yes** to "save these settings?"; **No** discards them. **Y** (reset) also puts the display
and fast-forward rows back to their defaults; your key and button bindings stay - each bindings page has its own reset (Y).

## Where files live

`%USERPROFILE%\AppData\LocalLow\DefaultCompany\Dpr\`

- `nn\save\...\SaveData.bin` / `Backup.bin` - your save, in the shipped format and separated by edition
- `pc_settings.ini` - the PC options (display, frame rate, fast-forward, key / button bindings)
- `Player.log` - the game's log (attach it to bug reports)

## FAQ

**Is this a decompilation?** Not in the strict sense. Brilliant Diamond is a Unity game compiled with IL2CPP: its C# was turned into
native ARM code, so the original source does not exist in the game. The C# in `Assets/Scripts` was restored from the shipped
executable - the type and member declarations are generated from the game's own metadata, and the method bodies are translated from
the decompiled machine code. It aims to behave exactly like the game; it is not byte-identical source.

**Why do I need my own dump?** The game's assets (models, textures, sounds, text) are not in this repository and never will be. The
setup exports them from your copy.

**Why isn't Wwise included?** The game's audio runs on Audiokinetic Wwise, whose Unity integration may not be redistributed. It is free
to download with an Audiokinetic account; the setup copies it in from your own install.

**Shining Pearl? Other versions?** Shining Pearl v1.3.0 support is experimental. The setup accepts Brilliant Diamond and Shining Pearl v1.3.0.

**PlayStation, Switch Pro or other controllers?** The game reads XInput (Xbox-type) gamepads directly. A DualShock 4, DualSense or
Switch Pro Controller works through Steam Input or DS4Windows, which present it as an Xbox pad.

**Other platforms (macOS, Linux, ...)?** The setup (`setup.cmd`) runs on Windows, and Windows is the platform we build and test. But
what the setup produces is an ordinary Unity 2019.4 project, and Unity can build it for any platform it supports - a port is open to
anyone. What a port needs today:

- the asset-bundle build (`Assets/Editor/BdspWinBuild`) targets Windows (`StandaloneWindows64`);
- the PC layer's gamepad (XInput), software keyboard, timer resolution and restart code use Windows APIs - they are fenced off with
  `UNITY_STANDALONE_WIN`, so another platform needs its own versions of them;
- the Wwise integration must include the target platform;
- the recovered shaders have only been tested with Direct3D 11.

Step by step for macOS: [docs/PORTING_MACOS.md](docs/PORTING_MACOS.md). Pull requests for other platforms are welcome.

**Can I share my build?** No. It contains the game's assets.

## Repository layout

| Path | What |
|---|---|
| `Assets/Scripts/{Game,AssetAssistant,DebugLog,nn,DOTweenPro}` | the game's C#, one file per type (`<Assembly>/<namespace>/<Type>.cs`) |
| `Assets/Scripts/_Ours/PcPlatform` | this project's PC layer: input and key bindings, display, fast-forward, saves, keyboard, frame clock |
| `Assets/_Ours` | this project's own assets (the one tracked asset folder - see its README) |
| `Assets/Editor` | editor tooling: the Windows build, audits, probes, the editor asset loader |
| `setup/` | the automated setup (`setup.py` and its stages); `setup/data` holds the shader source recovered from the game's compiled shaders and the tables that make every setup produce the same project |
| `Assets/Plugins/DOTween` | Demigiant DOTween 1.2.335, the version the game shipped |

The game's shipped code paths are kept: Switch-only code sits under `#if SWITCH`, and where the PC build changes a shipped statement
(for example the unlocked frame rate, `PC_UNLOCKED_FPS`) the shipped statement stays in the `#else` arm.

## Contributing

Bug reports and pull requests are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md). For a setup problem, attach `SetupWork\logs\`;
for a game problem, attach `Player.log`.

## Credits

- [AssetRipper](https://github.com/AssetRipper/AssetRipper) - exports the game's assets from your dump (downloaded by the setup).
- [UnityPy](https://github.com/K0lb3/UnityPy), [texture2ddecoder](https://github.com/K0lb3/texture2ddecoder), [Pillow](https://python-pillow.org/), [NumPy](https://numpy.org/) - read the shipped bundles and textures during the setup.
- [crunch](https://github.com/Unity-Technologies/crunch) (Unity Technologies' fork) - decodes the shipped crunched textures.
- [DOTween](http://dotween.demigiant.com/) by Demigiant - the tweening library the game ships with.
- [Audiokinetic Wwise](https://www.audiokinetic.com/) - the game's sound engine.
- [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) and [Ghidra](https://ghidra-sre.org/) - used to read the game's metadata and executable while making this project (not included).
- [OpenDPR](https://github.com/TeamLumi/opendpr) by Team Luminescent - prior art for rebuilding the game as a Unity project from your own dump.

## Legal

uDPR is a fan project. It is not affiliated with, endorsed or sponsored by Nintendo, The Pokémon Company, GAME FREAK inc., Creatures
Inc. or ILCA. Pokémon and all related names, characters and game content are trademarks and copyrights of their respective owners.
No game assets are included in this repository; `Assets/Scripts` holds C# restored from the game's executable, as described in the FAQ.

## License

This project's own work is released under the [MIT License](LICENSE). Third-party components keep their own licenses - see
[THIRD_PARTY.md](THIRD_PARTY.md).
