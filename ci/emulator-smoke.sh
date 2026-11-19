#!/usr/bin/env bash
# Runs inside an emulator: installs the debug APK, starts the overlay, captures a screenshot and the VALIS log.
set -u
OUT=${1:-smoke-out}; APK=${2:-app/build/outputs/apk/debug/app-debug.apk}
mkdir -p "$OUT"
adb install -r "$APK" || exit 1
adb shell appops set ai.valis.companion SYSTEM_ALERT_WINDOW allow
adb logcat -c
adb shell am start -n ai.valis.companion/ai.valis.app.MainActivity --ez valis_autostart true
sleep 25
adb exec-out screencap -p > "$OUT/overlay.png"
adb logcat -d -s VALIS.Character:V VALIS.Overlay:V AndroidRuntime:E Filament:V gltfio:V DEBUG:F libc:F > "$OUT/valis.log"
adb shell dumpsys window windows | grep -i "ai.valis" > "$OUT/windows.txt" || true
echo "--- VALIS log ---"; cat "$OUT/valis.log"
if grep -q "FATAL EXCEPTION" "$OUT/valis.log"; then echo "FAIL: app crashed"; exit 1; fi
if grep -qE "Fatal signal|SIGABRT|Postcondition|failed to link" "$OUT/valis.log"; then echo "FAIL: native crash or shader error"; exit 1; fi
if grep -q "character unavailable" "$OUT/valis.log"; then echo "FAIL: character did not load"; exit 1; fi
grep -q "character ready" "$OUT/valis.log" || { echo "FAIL: character never became ready"; exit 1; }
grep -q "first frame rendered" "$OUT/valis.log" || { echo "FAIL: no frame was rendered"; exit 1; }
echo "PASS: character loaded and rendered"
