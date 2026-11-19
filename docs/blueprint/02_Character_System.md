# 02 — Character System Specification (renderer, asset, integration)

Visuals: **VB-02** character system, **VB-03** rendering pipeline, **VB-04** rig & animation. State machine, behaviour and animation logic live in doc 04.
The character identity is fixed (F1): cobalt shell, near-black face, pearl ear linings, large expressive eyes, chest "V". **No redesign, no replacement.**

## 1. The asset, measured

### 1.1 Source asset (`VALIS_rigged.glb`, frozen)

| Property | Value |
|---|---|
| Nodes / skin joints / meshes / materials | 29 / 27 / 2 / 2 |
| `VALIS_body` | 286,174 verts, 500,000 tris, attributes `POSITION NORMAL TEXCOORD_0 JOINTS_0 WEIGHTS_0`, **26 morph targets** |
| `VALIS_mouth` | 225 verts, 384 tris, attributes `POSITION NORMAL COLOR_0 JOINTS_0 WEIGHTS_0`, **6 morph targets** (collapsed to a point at rest) |
| Materials | `material_0`: PBR (metallic 0.0, roughness 1.0), base-colour 4096² PNG + normal 2048² PNG, double-sided. `VALIS_mouth_interior`: white, emissive (0.01, 0.03, 0.18), double-sided |
| Rest bounds (body) | x ±0.367, y −0.499…+0.500, z ±0.252 (≈ 1.0 high, 0.73 wide incl. ears) |
| Animation | 48 clips, 30 fps, 1.03 s … 44.97 s, every clip keys all 29 nodes (T/R/S) + weights |
| Extensions | none (no Draco/meshopt/KTX2) |

### 1.2 Skeleton (27 joints, rotation-driven; non-root translation never animated)

```
root ─ hips ─┬─ spine ─ chest ─┬─ neck ─ head ─┬─ ear_1_L ─ ear_2_L
             │                 │               └─ ear_1_R ─ ear_2_R
             │                 ├─ shoulder_L ─ upperArm_L ─ lowerArm_L ─ hand_L
             │                 └─ shoulder_R ─ upperArm_R ─ lowerArm_R ─ hand_R
             ├─ upperLeg_L ─ lowerLeg_L ─ foot_L
             ├─ upperLeg_R ─ lowerLeg_R ─ foot_R
             └─ tail_1 ─ tail_2 ─ tail_3
```
The "arms" read as wing-like fins; the "legs" are short fins/feet below a floating body. There is **no jaw, tongue or eyeball bone**: mouth and gaze are morph-only.

### 1.3 Morph targets (verified names)

* `VALIS_body` (26): `eyeBlink_{L,R}`, `eyeSquint_{L,R}`, `eyeWide_{L,R}`, `eyeLook{Left,Right,Up,Down}_{L,R}`, `browUp_{L,R}`, `browDown_{L,R}`, `browInnerUp_{L,R}`, `browInnerDown_{L,R}`, `mouthSmile`, `mouthFrown`, `mouthWide`, `mouthPucker`.
* `VALIS_mouth` (6): `viseme_aa`, `viseme_oh`, `viseme_ou`, `viseme_ee`, `viseme_ih`, `viseme_fv`. **Missing** (must be approximated, doc 04 §8): closed-lip (B/M/P), `th`, `ss/ch`, `rr`, `nn/l`.

### 1.4 Clip inventory
Full per-clip measurements (duration, active joints >3°, root travel, scale deviation, loop error, active morphs) are in `appendix/clip_inventory.csv`. Summary groups used by the behaviour engine (doc 04 §4):

| Group | Clips (exact names) |
|---|---|
| Base loops / holds | `idle`, `weight_shift`, `sit_swing_legs`, `posture_crouch`, `posture_lean_{left,right,forward,back}` |
| Face poses (loop-safe, 3 s) | `expression_{happy,excited,surprised,curious,sleepy,sad,angry,shy,wink}` |
| Gestures | `wave_left`, `wave_right`, `nod`, `shake_head`, `tilt_head`, `shrug`, `bow`, `wiggle`, `flap`, `reach_ik`, `peek`, `look_around`, `look_targets` |
| Reactions | `startle`, `celebrate`, `jump`, `spin`, `turn_left` |
| Idle fidgets | `stretch`, `yawn`, `tail_wag`, `ear_twitch`, `dance_{bounce,sway,twist}` |
| Transitions | `sit_down`, `stand_up` |
| Speech body | `talk` |
| Reference takes (not used live) | `multi_sit_swing_look`, `living_idle_showcase` (45 s; used for QA and as a source of timing ideas only) |

## 2. Renderer architecture (Filament)

### 2.1 Components

| Component | Responsibility |
|---|---|
| `FilamentEngineHolder` | Process-wide `Engine` (one), backend OpenGL ES 3.x (Vulkan opt-in later), created lazily, destroyed after a dormant timeout (§6) |
| `CharacterSurface` | Owns `SurfaceView` (default) / `TextureView` (fallback). Handles `SwapChain` creation, translucency (`SurfaceHolder.setFormat(TRANSLUCENT)`, `setZOrderOnTop(true)` on the SurfaceView as validated in S1), resize |
| `AssetLoader` | `gltfio` `UbershaderProvider` (no runtime shader JIT → no first-frame hitches); loads `VALIS_runtime.glb` from assets on an IO thread; resolves entities by name |
| `RigBinder` | Builds `jointEntity[27]` and `morphTarget` indexes **by name**; hard-fails (with `RigMismatch` error + character fallback) if a required name is missing — never guesses |
| `PoseApplier` | Writes final local TRS to joint entities via `TransformManager.setTransform`, then `Animator.updateBoneMatrices()`; writes morph weights via `RenderableManager.setMorphWeights` for the face primitive and mouth primitive |
| `StageRig` | Camera, key light, IBL, color grading, view options |
| `FrameClock` | Throttled `Choreographer` loop with ACTIVE / IDLE / PAUSED modes |
| `RenderStats` | Frame time, dropped frames, GPU/RAM estimates → feeds adaptive quality |

### 2.2 Render thread model
`Main` (window/touch) → posts to `RenderThread` (single thread owns all Filament calls) ← `BehaviourExecutor` (5 Hz coroutine) posts immutable `PoseCommand`s through a lock-free queue. Pose math for 27 joints is trivially cheap and runs on the render thread each frame.

### 2.3 Rendering lifecycle

1. `OverlayService.onCreate` → `CharacterSurface` created, **not** attached.
2. Attach window → `SurfaceHolder.surfaceCreated` → create `SwapChain`.
3. `AssetLoader.load()` async (target ≤ 700 ms warm / ≤ 1.5 s cold on the mid-range reference device). While loading, the window shows nothing (summon animation starts when `AssetReady`).
4. `RigBinder.bind()` → `PoseRuntime.init(manifest)`.
5. `FrameClock.start(ACTIVE)`. Each frame: `Clock.tick(dt)` → `PoseRuntime.evaluate()` → `PoseApplier.apply()` → `renderer.render(view)`.
6. Sleep/tuck → `IDLE` (15 fps) or `PAUSED` (0 fps; resume on any event).
7. Dismiss → window removed, loop stopped, `SwapChain` destroyed; asset/engine retained for 120 s (warm re-summon) then destroyed.
8. `onTrimMemory(RUNNING_CRITICAL)` → immediately release engine; next summon is a cold load.

### 2.4 Lighting, camera, framing

* **Key light:** one directional light; no shadows (cost, and nothing to cast on). **Fill:** small IBL cubemap (256², KTX, ≤1 MB) tinted neutral-cool so the cobalt stays saturated; intensity tuned against golden renders.
* **Colour:** `ColorGrading` neutral/linear (no ACES filmic desaturation of the cobalt); bloom, DoF, SSAO **off**. Anti-aliasing: MSAA 4× when the surface config supports it with alpha, otherwise FXAA.
* **Background:** fully transparent (`View.BlendMode.TRANSLUCENT`, clear alpha 0).
* **Camera:** perspective, vertical FOV ≈ 25°, looking at the body centre; framing fits bounds with **20% headroom above** (jump/stretch) and 10% margin on the sides (ears + `flap`). Do not change FOV per state; the character "moves", the camera doesn't.
* **Scale:** user scale presets S/M/L = 0.75/1.0/1.25 of a 200 dp × 270 dp base viewport (px = dp × density). Render resolution scale 1.0, auto-drops to 0.75 if frame time > 14 ms for 2 s, recovers after 10 s stable.
* **Facing:** front-facing by default; ±35° yaw look-at via neck/head only (doc 04 §5); whole-body turns use `turn_left` mirrored by scale −1 on a *container* node only if S1 proves normal handedness safe; otherwise a body yaw rotation of the root joint.

### 2.5 Android GPU considerations

* Target OpenGL ES 3.0+ (all minSdk 26 devices with Filament support). Do not require Vulkan.
* Use the *ubershader* material set (fewer, pre-compiled variants); avoid per-frame material changes.
* KTX2/ETC2 (universally supported on GLES3) for textures; ASTC optional on devices that report it.
* Morph targets: only the face primitive carries them (§3). Verify the gltfio morph-buffer limits against the final target count (32) in S1.
* Thermal: query `PowerManager.getCurrentThermalStatus()` (API 29+) / `addThermalStatusListener`; at `THERMAL_STATUS_MODERATE` cap to IDLE fps; at `SEVERE` pause rendering and show a static pose.
* Battery saver on → cap to 15 fps and disable spontaneous large motions.
* Expect OEM variance (transparency, GPU drivers): the S1 device matrix must include at least three GPU families (Adreno, Mali, one other available).

## 3. Runtime asset specification (`VALIS_runtime.glb`) — Task T-ASSET

Built by `tools/asset-pipeline`; the source GLB is never edited.

| Requirement | Budget / rule |
|---|---|
| Triangles | body ≤ 38k, face primitive included; total ≤ 45k |
| **Primitive split** | `VALIS_face` (head front, ≈ 10–14k verts, **only primitive with morph targets**) · `VALIS_body` (rest) · `VALIS_mouth` (unchanged semantics) |
| Skin | same 27 joints, same names, same hierarchy, ≤ 4 influences/vertex |
| Morph targets | exactly the 26 + 6 verified names, same order, same semantic |
| Textures | base colour ≤ 2048² (KTX2 UASTC→ETC2 transcode, or pre-transcoded ETC2); normal ≤ 2048², **baked from the 500k-tri source** |
| File size | ≤ 12 MB (aim 6–9 MB) |
| Materials | same two, same factors; roughness/metal preserved |
| Skeleton rest pose | bit-identical joint transforms to the source |
| Verification | automated: names/order/counts/hierarchy checks; visual: golden renders (front, ¾L, ¾R, side, back) with mean ΔE₀₀ ≤ 6 inside the silhouette; manual TD sign-off on all nine expressions and all six visemes |

**Decimation caveat (Risk R1):** shape-key-bearing meshes cannot be collapsed blindly. The accepted routes are (a) retopologise/decimate the *base* mesh and transfer all shape keys by surface/data transfer, then verify each morph visually, or (b) rebuild the face region as a clean low-poly mesh with authored morphs. gltfpack/meshopt simplification is *not* assumed to preserve morphs — verify before use. If the budget cannot be met without visible loss, the fallback ladder is: 60k tris → 80k tris (Tier-B devices only) with the render-resolution scale as the pressure valve.

**Asset QA tickets for the 3D TD:** T-ASSET-01 decimate+bake · T-ASSET-02 face split · T-ASSET-03 KTX2/ETC2 · **T-ASSET-04 fix helmet-shell separation in `droop`, `bow`, `expression_shy`** · T-ASSET-05 add missing visemes (closed-lip/B-M-P, th, ss/ch) *if budget allows; otherwise approximate (doc 04 §8)*.

## 4. Clip bake (`valis_anim.v1`) — Task T-BAKE

Input: `VALIS_runtime.glb` (or the source; the animation data is identical). Output: `valis_anim.v1.bin` + `valis_anim.v1.json` shipped in app assets.

Per clip the bake emits: `name`, `duration`, `fps=30`, joint list, quantised rotation keys (16-bit-per-component normalised quaternions), root/hips translation keys, scale keys only where deviation ≥ 0.02, morph keys **split by channel group** (`BLINK`, `GAZE`, `BROW`, `LID` (squint/wide), `MOUTH` (smile/frown/wide/pucker), `VISEME`), `loopable` flag (end vs start error ≤ 5° and ≤ 1 cm), `meaningfulMask` (joint set whose rotation range ≥ 3°, minus the "float set" {legs, ears, tail} unless an override says the clip is *about* them), and `tags`. A hand-maintained `clip_overrides.json` fixes masks (e.g. `tail_wag → TAIL`, `ear_twitch → EARS`, `wave_right → ARM_R + SHOULDER_R`).

Data size estimate: 48 clips × avg 3.6 s × 30 fps × 27 joints × 8 B ≈ 1.5 MB raw → ≈ 0.7 MB quantised (the 45 s showcase excluded from the live set).

## 5. Character integration specification (what the rest of the app may rely on)

```kotlin
interface CharacterRuntime {
  val state: StateFlow<CharacterState>          // DORMANT, SUMMONED, IDLE, LISTENING, THINKING, SPEAKING, ACTING, INTERRUPTED, SLEEPING, ERROR
  fun onEvent(e: CharacterEvent)                // the only inbound path (doc 01 §2.1)
  fun setVisemeSource(src: VisemeSource?)       // amplitude or timed viseme stream (doc 04 §8)
  fun setLookTarget(t: LookTarget?)             // screen point, touch point, or user-forward
  fun setViewport(sizePx: Size, scale: ScalePreset)
  val capabilities: CharacterCapabilities       // clips, joints, morphs actually bound (from RigBinder)
  suspend fun warmUp()                          // load asset + bind + first frame
  fun release(level: ReleaseLevel)              // PAUSE | DROP_ASSET | DROP_ENGINE
}
```
The existing repo interface `CharacterRenderer` (`playAnimation`, `setMorphTarget`, `setBoneRotation`, …) is **kept as the low-level renderer facade** implemented by `PoseApplier`; `CharacterRuntime` sits above it. `CharacterStateMachine` gains `SUMMONED` and `ERROR` (non-breaking additions).

## 6. Error handling

| Failure | Behaviour |
|---|---|
| Asset missing/corrupt | Fall back to a 2D static pearl "V" badge window; log `ASSET_LOAD_FAILED`; never crash the service |
| `RigMismatch` (name not found) | Disable the dependent layer (e.g. no mouth) and continue; surface in debug overlay |
| Surface lost (`surfaceDestroyed`) | Destroy `SwapChain`, wait for new surface, resume |
| GL context loss / driver reset | Recreate engine; cold re-load |
| Frame time > 33 ms for 3 s | Drop resolution scale → FXAA → IDLE fps → static pose, in that order |
| OOM | `release(DROP_ENGINE)`, retry once on next summon |

## 7. Testing requirements

* **Unit:** bake tool (golden JSON for 3 clips), rig name binder, loop-error calc, mask derivation.
* **Golden renders:** deterministic pose set (rest + 9 expressions + 6 visemes + 5 gestures) rendered on the reference devices; compared to approved references (ΔE and silhouette IoU ≥ 0.97).
* **Instrumented:** load/cold/warm timings; surface loss/recovery; rotate/resize; 30-minute soak (no leak: RSS growth ≤ 10 MB).
* **Perf gate:** budgets in doc 01 §5 on the mid-range reference device.

## 8. Acceptance criteria (character system)

1. `VALIS_runtime.glb` meets §3 and the TD signs off identity fidelity.
2. All 27 joints and 32 morph names bind with zero mismatches.
3. Rest pose renders within ΔE tolerance of the golden set on two GPU families.
4. 30 fps active, budgets met on the mid-range device; thermal and battery-saver degradation verified.
5. Cold load ≤ 1.5 s, warm re-summon ≤ 400 ms.
6. No crash across 100 summon/dismiss cycles and 30 surface-loss events.
