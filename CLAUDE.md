# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## What this repo is

A library of **59 film styles**, each a `styles/<slug>/` folder containing:

| File | Role |
|---|---|
| `style.json` | the only metadata source (slug, num, en/cn names, category, film title, taglines, `frame_sec`, `dur`) |
| `STYLE.md` | the style's invariants: look, materials, colour logic, type, motion, camera grammar, sound palette, native moves, pitfalls |
| `DEMO.md` | how the demo film was made (story, shots, score, build notes); the only place the "LemoLab × Claude Opus 5.5" sign-off lives |
| `demo/` | committed demo source with a one-command `build.sh` and `CREDITS` |
| `demo/stills/styleframe.jpg` | gallery card |
| `<slug>.mp4`, `<slug>.srt`, `poster.jpg` | the demo film (gitignored; shipped via GitHub Releases) |

Everything in a film is generated from code: no stock footage, no video generation. The demos are **references for technique, never for story** — a user's film must differ in structure, opening, signature shot, camera path, score shape and ending.

## Commands

Run from the repo root. Python is `.venv/bin/python` (Windows: `.venv/Scripts/python.exe`).

```sh
sh plugin/skills/lemo-opuscar/scripts/setup.sh deps        # core: npm, headless Chromium, .venv (~350 MB)
sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice  # Kokoro TTS + edge-tts + faster-whisper
sh plugin/skills/lemo-opuscar/scripts/setup.sh deps music  # numba, for pluck.py
sh tools/fetch.sh instruments <lib>|all | hdri | voice     # sample libraries, HDRIs, Kokoro model
```

Render and check a film page (any folder with `index.html`; `<demo>` = that folder):

```sh
node core/render/still.mjs <demo> 1.5 12 --range 0:50:2      # review stills → <demo>/stills/
node core/render/video.mjs <demo> --fps 24 --workers 3       # → <demo>/out/video.mp4 (one --out per render)
node core/render/events.mjs <demo>                           # export DUR + EV → events.json
node core/render/readcheck.mjs <demo>                        # on-screen text held long enough to read
.venv/bin/python core/render/sheet.py out.jpg img… --cols 4  # contact sheet
.venv/bin/python core/render/srt.py cues.json out.srt
sh core/render/mux.sh video.mp4 mix.wav out.mp4 24 [grain]   # mux + two-pass loudnorm −14 LUFS
```

Voice and audio:

```sh
.venv/bin/python core/tts/tts.py lines.json out/             # Kokoro, offline, English
.venv/bin/python core/tts/tts_zh.py lines.json out/          # edge-tts, online, Chinese
.venv/bin/python core/tts/asr_check.py lines.json out/ --lang en|zh   # every line must transcribe back
```

Maintainer-only (never for a user's film):

```sh
python3 styleboard/build.py                                  # style.json → catalog.json, index.html, README/AGENTS generated parts
python3 styleboard/build.py --frames <slug>                  # docs/frames/<slug>.jpg at frame_sec
sh styleboard/frames.sh <slug>                               # gallery card from demo/stills/styleframe.jpg
python3 tools/release.py check --strict <slug>               # the gate for a new/changed style
sh tools/publish.sh                                          # build.py + web cuts + pack/upload/verify Releases
sh tools/web_cuts.sh                                         # 720p cuts → .release/web/
python3 tools/directory.py <version> --into ../lemo-opuscar-directory   # plugin-directory edition (orphan branch)
```

There is no unit-test suite. Verification is: `readcheck.mjs`, `asr_check.py`, `mux.sh` loudness report, `ffmpeg -af ebur128` / `blackdetect` on the final file, one full-speed viewing with sound, and for library changes `release.py check --strict`.

## Architecture

**The page contract** — every film is a web page, and time is the only input:

```js
window.DUR = 54.2;
window.render = (t) => { … };   // deterministic: no Date.now(), no unseeded Math.random(), no cross-frame state
window.READY = true;            // once fonts and images are loaded
window.EV = [{t, type, …}];     // optional sound/cue events
window.TEXTS = (t) => [{id, text, x0, y0, x1, y1}];   // optional, for readcheck
```

`core/render/page.mjs` + `serve.mjs` serve the repo root on 127.0.0.1 (film folders outside the repo are mounted at `/@film/`), open it in headless Chromium, and wait up to 180 s for `READY`. A page error or a failed script/module load is fatal; a missing fetch/image/font only prints `optional file missing`. Pages use **absolute URLs** (`/core/lib.js`, `/node_modules/three/…`), never `../..`; scripts and `build.sh` use `$LIB`.

**The pipeline** (`TECHNIQUE.md`):

```
timeline.js (single source of truth: sections, tempo, hits)
  ├─ picture: render(t) → headless Chrome, JPEG frames → ffmpeg → video.mp4
  ├─ voice:   TTS → asr_check (word timings) → lines.json
  ├─ music:   sampler.py / pluck.py / numpy, from the same cue map → stems
  ├─ foley:   sfx.py driven by window.EV
  └─ subs:    burned-in captions in the page + .srt from srt.py
mix.py → out/mix.wav → mux.sh (loudnorm −14 LUFS, grain in ffmpeg) → <name>.mp4
```

**Layout**

| Path | What it holds |
|---|---|
| `AGENTS.md` | the agent's entry point: Start → Style and story → Workflow → Where things go |
| `DIRECTOR.md` | directing method: brief, benchmark, treatment, look proof, sound, rhythm, camera, performance, failure list, delivery, copyright |
| `TECHNIQUE.md` | how the films are built; `core/README.md` is the exact command/flag/exit-code reference |
| `MY-STYLES.md` | user-owned styles in `~/lemo-my-styles/` (change a library style or start blank) |
| `MAINTAINING.md` | owner-only: add/revise a style, register, gates, publish, directory edition |
| `core/` | shared toolkit: `lib.js` (seeded rand, easing, noise), `render/`, `tts/`, `audio/`, `three/post.js`, `post/crt.js`, `fonts/`, `assets/` |
| `styles/` | the 59 styles + `_template/` |
| `styleboard/` | gallery builder and site templates |
| `tools/` | `fetch.sh`, `release.py`, `publish.sh`, `web_cuts.sh`, `directory.py` |
| `plugin/` | the Claude plugin wrapper; `scripts/setup.sh` finds/clones/updates the library and prints `LIB=<path>` |
| `films/<name>/` | a user's film project (gitignored); in skill mode it's `<name>/` in the user's folder |

**Two modes.** Clone mode: `films/<name>/`, `LIB` is the repo. Skill mode: the project is outside the library, pages are mounted at `/@film/`, and `build.sh` starts with `LIB=<path printed by setup.sh>`.

## Conventions and gotchas

- **Never edit `core/` or `styles/` to make a user's film.** Copy what you need into the project folder.
- **Treatment before demo.** Write `TREATMENT.md` (three candidate structures + choice) before opening `DEMO.md` or demo code. Exception: Edit & Documentary styles gather material with `demo/tools/footage.py` first.
- **Generated files, never hand-edited:** `styleboard/catalog.json`, the generated parts of `README.md` / `README.zh-CN.md` / `styles/README.md` / the style list in `AGENTS.md`, `docs/frames/`, `styleboard/img/`. Change `styles/*/style.json` and rerun `build.py`.
- **No LemoLab credit or watermark in a user's film.** Check with `grep -rniE "lemo ?lab|opus 5\.5" <project folder>` (excluding `LICENSE`, `CREDITS`, `LIB=` lines) and watch the final seconds.
- **Determinism is a hard requirement.** Any frame may be rendered alone, in any order, by any worker; reseed per frame from `t`.
- **Effects that follow a subject** go through one world→screen function; never hand-type screen coordinates.
- **Assets:** CC0 / CC BY / OFL only, each listed in `CREDITS`; other open licences only after telling the user the terms. Facts on screen need `FACTS.md` (claim, URL, quoted wording).
- **Fonts** are self-hosted per project; `core/fonts/` has ~200 ZCOOL glyphs only. Subset CJK via the Google Fonts `&text=` API.
- **`styles/*/demo/**` media, fonts, models and `TREATMENT.md` are gitignored**; only code, `CREDITS` and named review stills are committed.
- **Platform:** developed on macOS; on Windows the guides say use WSL. On this machine Node 24, Python 3.12 and ffmpeg exist, and Git Bash runs the tools; set `PLAYWRIGHT_CHROME` to an installed Chromium if Playwright can't find one (see `films/mpemba/build.sh`).
- **Renders are expensive:** `--workers 3` when several films run in parallel, up to 6 for one; set `RENDER_SLOTS` to cap concurrent full renders machine-wide. Each render needs its own `--out`.
