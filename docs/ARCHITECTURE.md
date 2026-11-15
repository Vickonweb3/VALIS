# VALIS implementation architecture

## Build sequence after model + rigging

### Milestone 1 — Native character renderer
- Import the exact rigged GLB into Android assets.
- Load it through Filament.
- Confirm materials, skeleton, clip names and morph targets survive import.
- Implement animation playback and deterministic transitions.
- Profile memory, frame time and thermal behaviour on the target Android device.

### Milestone 2 — Floating character host
- Attach the renderer surface to the WindowManager overlay host.
- Implement drag, snap-to-corner and safe screen margins.
- Add summon/hide lifecycle and touch target sizing.
- Respect Android overlay restrictions and user-granted permission.

### Milestone 3 — Living movement system
- Build an animation catalogue from clips actually present in the model.
- Create a priority-based state machine and interrupt rules.
- Add procedural head/eye/torso movement only for bones verified in the rig.
- Add layered animation only where tracks can be safely masked; avoid conflicting full-body clips.
- Add spontaneous idle scheduling with repetition avoidance and natural pauses.
- Drive expression and viseme targets from character state and speech timing.

### Milestone 4 — Voice and wake word
- Lightweight wake-word path, foreground microphone lifecycle, speech input/output.
- Interruptible speech and state transitions.
- Audio-reactive mouth/viseme control.

### Milestone 5 — Vision and phone actions
- User-consented screen capture.
- Separate authorized accessibility/action layer.
- Tool permissions, confirmation for consequential actions, and verified outcomes.

### Milestone 6 — Model integration, memory and hardening
- Connect the selected multimodal inference endpoint after its runtime and license are verified.
- Keep durable memory separate from model weights.
- Privacy controls, failure handling, telemetry opt-in and device compatibility testing.

## High-freedom movement design

The rig is the physical capability boundary. High freedom comes from combining:
1. Existing authored clips as expressive motion primitives.
2. Procedural control of verified bones.
3. Facial morph targets and eye controls.
4. Safe animation layers with masks and priorities.
5. A behaviour scheduler that chooses when and why to move.

"Spontaneous" means the character can choose appropriate idle behaviours without a user prompt, not that it moves continuously or randomly without regard to context.

## Android constraints
Overlay visibility is permission-gated and not guaranteed above secure/system surfaces. Foreground services and microphone access are subject to Android version and device restrictions. The app must explain and respect those limits.
