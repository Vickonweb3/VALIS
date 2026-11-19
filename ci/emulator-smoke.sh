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
adb logcat -d -s VALIS.Character:V VALIS.Overlay:V AndroidRuntime:E Filament:V gltfio:V > "$OUT/valis.log"
adb shell dumpsys window windows | grep -i "ai.valis" > "$OUT/windows.txt" || true
echo "--- VALIS log ---"; cat "$OUT/valis.log"
# Fail the job only on a hard crash; character errors are reported in the log and screenshot.
if grep -q "FATAL EXCEPTION" "$OUT/valis.log"; then echo "app crashed"; exit 1; fi
