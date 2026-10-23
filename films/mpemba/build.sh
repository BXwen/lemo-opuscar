#!/bin/sh
# 《姆潘巴悬案》 one-command build: frames → video → score → mastered film
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$(cd "$HERE/../.." && pwd)}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the library folder"; exit 1; }
# reuse an already-installed Chromium instead of downloading one
export PLAYWRIGHT_CHROME="${PLAYWRIGHT_CHROME:-$LOCALAPPDATA/ms-playwright/chromium-1223/chrome-win64/chrome.exe}"
export CHROME_PATH="$PLAYWRIGHT_CHROME"
cd "$LIB"
node core/render/events.mjs "$HERE"
node core/render/video.mjs "$HERE" --fps 30 --out "$HERE/out/video.mp4"
"$LIB/.venv/bin/python" "$HERE/music.py" "$HERE/out/mix.wav"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/mpemba.mp4" 30 0
