# VALIS Character Runtime

Phase 1 browser-based development harness for the actual VALIS rigged GLB.

## Current capabilities
- Load a local GLB/GLTF file. The model is processed locally in the browser; it is not uploaded.
- Inspect meshes, skinned meshes, bones, animation clips, materials and morph targets.
- Play, pause, stop, scrub and change playback speed for animation clips.
- Cross-fade when switching clips.
- Apply facial morph presets and manually adjust detected morph targets.
- Toggle spontaneous idle behaviour using randomized timing and a recent-action avoidance window.
- Orbit, zoom, reset camera and fullscreen preview.

## Run locally
Requires Node.js 20.19+ or 22.12+.

```bash
npm install
npm run dev
```

Open the local Vite URL and load a copy of `VALIS_rigged.glb`.

## Important boundaries
- This is a development preview, not the final Android runtime.
- Autonomous idle currently selects from existing animation clips; it is not generative motion.
- Facial presets use detected morph targets. If an animation clip also animates those same targets, stop that clip before testing manual facial controls.
- This build does not yet blend arbitrary full-body clips simultaneously. Many full-body clips animate overlapping bones; blindly blending them can create conflicting poses. A later motion-layer system needs track masks or procedural controls.
- The original GLB is never modified.
- Android overlay, microphone, wake-word, screen vision, AI inference and persistent memory are not included yet.

## Next milestones
1. Validate all clips and facial morph targets visually.
2. Build safe animation layers and procedural head/eye movement.
3. Add behaviour priorities, interruption and event-driven reactions.
4. Port the character runtime to the selected Android rendering stack.
