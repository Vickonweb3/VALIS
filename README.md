# VALIS — Android Character Runtime

Native Android foundation for VALIS. This repository is being built around the real character runtime and floating companion, not a browser-based GLB viewer.

## Current milestone

This commit replaces the accidental web viewer with an Android/Kotlin project foundation.

Included:
- Native Android application module.
- Minimal launch activity; this is a developer shell, not the final product UI.
- Overlay permission flow and a foreground overlay service foundation.
- Character runtime interfaces separating rendering, animation and behaviour.
- Filament Android dependency reserved for the native GLB renderer.

Not yet implemented:
- Actual GLB loading/rendering in Filament.
- Binding VALIS's specific skeleton and animation clips.
- Autonomous procedural movement and animation blending.
- Wake-word, speech, vision, AI inference, memory or phone actions.

## Project layout

- `app/`: Android application.
- `app/src/main/java/ai/valis/app/`: application and overlay lifecycle.
- `app/src/main/java/ai/valis/character/`: renderer/animation/behaviour contracts.
- `docs/ARCHITECTURE.md`: implementation boundaries and next steps.

## Build

Requires Android Studio or a compatible Android SDK + JDK 17 + Gradle.

```bash
./gradlew :app:assembleDebug
```

The Gradle wrapper is not committed in this initial scaffold. Generate it with an installed Gradle distribution using `gradle wrapper`, or open the project in Android Studio and let it configure Gradle.

## Development order

1. Integrate and validate the supplied rigged GLB with Filament.
2. Map the model's real animation clip names and skeleton.
3. Implement animation state control and safe transitions.
4. Render the character inside the overlay service.
5. Add autonomous behaviour and procedural movement.
6. Add wake-word and voice interaction.
7. Add permitted screen understanding and phone actions.
8. Build the polished companion settings UI last.

The character asset itself is intentionally not committed until the final GLB is supplied and its size/licensing are checked.
