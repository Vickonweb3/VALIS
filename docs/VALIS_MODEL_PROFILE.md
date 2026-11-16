# VALIS rigged model profile

Source inspected: `VALIS_rigged.glb` from the project Library.

## Binary validation
- Container: GLB / glTF 2.0
- File size: 38,962,564 bytes (~37.2 MiB)
- Declared GLB length matches the file length
- Scene count: 1
- Nodes: 29
- Meshes: 2
- Skins: 1
- Skin joints: 27
- Animation clips: 48

## Rig node names
`root`, `hips`, `spine`, `chest`, `neck`, `head`,
`shoulder_L`, `upperArm_L`, `lowerArm_L`, `hand_L`,
`upperLeg_L`, `lowerLeg_L`, `foot_L`,
`shoulder_R`, `upperArm_R`, `lowerArm_R`, `hand_R`,
`upperLeg_R`, `lowerLeg_R`, `foot_R`,
`tail_1`, `tail_2`, `tail_3`,
`ear_1_L`, `ear_2_L`, `ear_1_R`, `ear_2_R`.

Additional scene nodes: `VALIS_body`, `VALIS_mouth`.

## Animation clips
`idle`, `wave_left`, `wave_right`, `nod`, `shake_head`, `tilt_head`,
`look_around`, `stretch`, `yawn`, `jump`, `spin`, `bow`, `shrug`,
`wiggle`, `flap`, `startle`, `celebrate`, `droop`, `peek`, `tail_wag`,
`ear_twitch`, `weight_shift`, `dance_bounce`, `dance_sway`, `dance_twist`,
`turn_left`, `sit_down`, `sit_swing_legs`, `stand_up`, `posture_crouch`,
`posture_lean_left`, `posture_lean_right`, `posture_lean_forward`,
`posture_lean_back`, `expression_happy`, `expression_excited`,
`expression_surprised`, `expression_curious`, `expression_sleepy`,
`expression_sad`, `expression_angry`, `expression_shy`, `expression_wink`,
`talk`, `look_targets`, `reach_ik`, `multi_sit_swing_look`,
`living_idle_showcase`.

## Integration notes
- Use the exact clip names above; do not invent aliases.
- Map animation states to these clips in the behaviour controller.
- Test whether clips are authored as full-rig tracks before layering/blending them.
- Validate mouth/viseme support separately; a node named `VALIS_mouth` alone does not prove phoneme blendshapes exist.
- Use only bones present in the skin for procedural motion.
- Runtime import, materials, scale, origin, frame rate and device performance still need testing in the Android renderer.

The GLB itself has not yet been committed to this repository. Git LFS is configured so the binary can be added without placing a large model directly in ordinary Git history.
