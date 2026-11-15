# VALIS integration checklist

## Character
- [ ] Add the rigged GLB under app/src/main/assets/valis/.
- [ ] Inventory real clip, bone, morph and viseme names.
- [ ] Implement and validate the concrete Filament renderer.
- [ ] Test animation blending only on verified compatible tracks.

## Android
- [ ] Test overlay permission, dragging, snapping and safe areas.
- [ ] Test foreground-service restrictions and notification.
- [ ] Add licensed "Yo VALIS" wake-word engine/model.
- [ ] Add MediaProjection foreground capture service after consent.
- [ ] Implement user-enabled accessibility actions with allow-list.

## Intelligence
- [ ] Verify model licence and commercial-use terms.
- [ ] Deploy inference endpoint and define audio/image request schema.
- [ ] Configure secrets outside source control.
- [ ] Add streaming audio, latency handling and fallback paths.
- [ ] Add memory controls and privacy disclosures.

This repository currently contains integration contracts, not a completed renderer, wake-word model or deployed inference service.
