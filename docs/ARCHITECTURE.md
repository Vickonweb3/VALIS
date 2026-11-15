# VALIS architecture
Character-first Android companion. The final settings/home UI is deferred.
- Overlay: visibility, drag and touch.
- Character renderer: supplied GLB, skeleton, animation clips and morph targets.
- Behaviour: HIGH movement freedom through authored clips plus safe procedural controls; SPONTANEOUS idle with context, cooldown and repetition avoidance.
- Voice: on-demand speech recognition and TTS. A separate licensed low-power wake-word model is still required.
- Vision: MediaProjection requires fresh user consent and a foreground capture service.
- Actions: Accessibility must be explicitly enabled; use an allow-list and confirmations.
- Intelligence: secure model endpoint, provider adapter and tool broker.
- Memory: separate local store, inspectable and clearable.

Android cannot guarantee overlays above secure/system screens. Background microphone use is restricted. The actual GLB, concrete Filament renderer, wake-word runtime, capture service, deployed model endpoint and device testing remain to be integrated.
