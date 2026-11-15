import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import './style.css';

const $ = (id) => document.getElementById(id);
const stage = $('drop-zone');
let renderer, scene, camera, orbit, clock, mixer, modelRoot;
let activeAction = null;
let actions = new Map();
let morphEntries = [];
let currentFileUrl = null;
let autonomyTimer = null;
let autonomyEnabled = false;
let recentIdle = [];
const IDLE_POOL = ['idle','look_around','weight_shift','tail_wag','ear_twitch','wiggle','peek','stretch','yawn','posture_lean_left','posture_lean_right'];
const FACE_PRESETS = {
  neutral: {},
  happy: { mouthSmile: 0.85, browUp_L: 0.12, browUp_R: 0.12 },
  curious: { eyeWide_L: 0.28, eyeWide_R: 0.28, browUp_L: 0.7, browUp_R: 0.7, browInnerUp_L: 0.35, browInnerUp_R: 0.35 },
  surprised: { eyeWide_L: 0.85, eyeWide_R: 0.85, browUp_L: 0.9, browUp_R: 0.9, mouthWide: 0.35 },
  sleepy: { eyeSquint_L: 0.65, eyeSquint_R: 0.65 },
  sad: { mouthFrown: 0.8, browInnerUp_L: 0.6, browInnerUp_R: 0.6 }
};
function setStatus(message, ready = false) {
  $('runtime-status').innerHTML = '<i></i> ' + message;
  $('runtime-status').classList.toggle('ready', ready);
}
function initRenderer() {
  if (renderer) return;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x17151e);
  camera = new THREE.PerspectiveCamera(34, 1, 0.01, 100);
  camera.position.set(0, 1.25, 3.8);
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  stage.prepend(renderer.domElement);
  orbit = new OrbitControls(camera, renderer.domElement);
  orbit.enableDamping = true;
  orbit.target.set(0, 0.9, 0);
  scene.add(new THREE.HemisphereLight(0xcfc5ff, 0x28202e, 2.1));
  const key = new THREE.DirectionalLight(0xffffff, 2.7);
  key.position.set(3, 5, 4);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x8264ff, 2.2);
  rim.position.set(-4, 2, -3);
  scene.add(rim);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(2.5, 64), new THREE.MeshStandardMaterial({ color: 0x211e2a, roughness: 0.92 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.015;
  scene.add(floor);
  clock = new THREE.Clock();
  resizeRenderer();
  window.addEventListener('resize', resizeRenderer);
  animate();
}
function resizeRenderer() {
  if (!renderer) return;
  const w = stage.clientWidth, h = stage.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.05);
  if (mixer) mixer.update(delta);
  if (orbit) orbit.update();
  if (renderer && scene && camera) renderer.render(scene, camera);
  if (activeAction) {
    $('time-label').textContent = activeAction.time.toFixed(2) + 's';
    const duration = activeAction.getClip().duration || 1;
    $('timeline').value = String(Math.min(1, activeAction.time / duration));
  }
  const now = performance.now();
  if (!animate.samples) animate.samples = [];
  animate.samples.push(now);
  animate.samples = animate.samples.filter(t => now - t < 1000);
  if (animate.samples.length > 1) $('fps-label').textContent = Math.round(animate.samples.length) + ' FPS';
}
function disposeModel() {
  if (!modelRoot) return;
  if (mixer) mixer.stopAllAction();
  scene.remove(modelRoot);
  modelRoot.traverse(obj => {
    if (obj.isMesh) {
      obj.geometry.dispose();
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      mats.forEach(mat => { if (mat) mat.dispose(); });
    }
  });
  modelRoot = null;
  mixer = null;
  actions.clear();
  morphEntries = [];
  activeAction = null;
}
function collectMorphTargets(root) {
  const found = [];
  root.traverse(obj => {
    if (!obj.isMesh || !obj.morphTargetDictionary || !obj.morphTargetInfluences) return;
    Object.entries(obj.morphTargetDictionary).forEach(([name, index]) => found.push({
      name, index, mesh: obj, viseme: name.startsWith('viseme_')
    }));
  });
  return found;
}
function morphLookup(name) {
  return morphEntries.find(entry => entry.name === name);
}
function setMorph(name, value) {
  const entry = morphLookup(name);
  if (entry) entry.mesh.morphTargetInfluences[entry.index] = THREE.MathUtils.clamp(value, 0, 1);
}
function resetMorphs() {
  morphEntries.forEach(entry => { entry.mesh.morphTargetInfluences[entry.index] = 0; });
}
function renderMorphControls() {
  const facial = morphEntries.filter(entry => !entry.viseme);
  const visemes = morphEntries.filter(entry => entry.viseme);
  $('morph-count').textContent = facial.length + ' CONTROLS';
  function build(items, target) {
    target.innerHTML = '';
    if (!items.length) {
      target.innerHTML = '<p class="helper">No controls detected.</p>';
      return;
    }
    items.forEach(item => {
      const wrap = document.createElement('div');
      wrap.className = 'morph-control';
      const label = document.createElement('label');
      label.textContent = item.name;
      const output = document.createElement('output');
      output.textContent = '0.00';
      const input = document.createElement('input');
      input.type = 'range';
      input.min = '0'; input.max = '1'; input.step = '0.01';
      input.value = String(item.mesh.morphTargetInfluences[item.index] || 0);
      input.addEventListener('input', () => {
        const value = Number(input.value);
        item.mesh.morphTargetInfluences[item.index] = value;
        output.textContent = value.toFixed(2);
      });
      wrap.append(label, output, input);
      target.append(wrap);
    });
  }
  build(facial, $('morph-controls'));
  build(visemes, $('viseme-controls'));
  $('reset-face').disabled = facial.length === 0;
  document.querySelectorAll('[data-face]').forEach(button => { button.disabled = facial.length === 0; });
}
function setFacePreset(name) {
  resetMorphs();
  Object.entries(FACE_PRESETS[name] || {}).forEach(([key, value]) => setMorph(key, value));
  renderMorphControls();
}
function playClip(name, options = {}) {
  const loop = options.loop ?? false;
  const fade = options.fade ?? 0.3;
  const restart = options.restart ?? true;
  if (!mixer || !actions.has(name)) return;
  const next = actions.get(name);
  if (activeAction === next && !restart) return;
  next.reset();
  next.enabled = true;
  next.setEffectiveTimeScale(Number($('speed-select').value || 1));
  next.setEffectiveWeight(1);
  next.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, loop ? Infinity : 1);
  next.clampWhenFinished = !loop;
  if (activeAction && activeAction !== next) activeAction.crossFadeTo(next, fade, true);
  next.fadeIn(fade).play();
  activeAction = next;
  $('clip-select').value = name;
  $('play-pause').innerHTML = 'Ⅱ <span>Pause</span>';
}
function stopPlayback() {
  if (!mixer) return;
  mixer.stopAllAction();
  activeAction = null;
  $('play-pause').innerHTML = '▶ <span>Play</span>';
}
function setAutonomy(enabled) {
  autonomyEnabled = enabled;
  $('autonomy-label').textContent = enabled ? 'AUTONOMY ACTIVE' : 'AUTONOMY OFF';
  document.querySelector('.autonomy-state').classList.toggle('active', enabled);
  if (autonomyTimer) clearTimeout(autonomyTimer);
  if (enabled) scheduleIdleAction(900);
  else $('next-action').textContent = '—';
}
function scheduleIdleAction(delay = 4000) {
  if (!autonomyEnabled) return;
  if (autonomyTimer) clearTimeout(autonomyTimer);
  $('next-action').textContent = 'choosing…';
  autonomyTimer = setTimeout(() => {
    if (!autonomyEnabled) return;
    const available = IDLE_POOL.filter(name => actions.has(name) && !recentIdle.includes(name));
    const pool = available.length ? available : IDLE_POOL.filter(name => actions.has(name));
    if (!pool.length) {
      $('next-action').textContent = 'no idle clips';
      scheduleIdleAction(5000);
      return;
    }
    const choice = pool[Math.floor(Math.random() * pool.length)];
    recentIdle = recentIdle.slice(-3).concat(choice);
    $('next-action').textContent = choice.replaceAll('_', ' ');
    playClip(choice, { loop: false, fade: 0.45 });
    const duration = actions.get(choice).getClip().duration;
    scheduleIdleAction(Math.max(duration * 1000 + 500, 3500) + Math.random() * 2600);
  }, delay);
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]));
}
function buildDiagnostics() {
  let meshCount = 0, skinCount = 0;
  const materials = new Set();
  modelRoot.traverse(obj => {
    if (obj.isMesh) {
      meshCount++;
      (Array.isArray(obj.material) ? obj.material : [obj.material]).forEach(mat => materials.add(mat));
    }
    if (obj.isSkinnedMesh) skinCount++;
  });
  const bones = [];
  modelRoot.traverse(obj => { if (obj.isBone) bones.push(obj.name); });
  const morphCount = morphEntries.length;
  $('info-meshes').textContent = meshCount;
  $('info-bones').textContent = bones.length;
  $('info-animations').textContent = actions.size;
  $('info-morphs').textContent = morphCount;
  $('info-materials').textContent = materials.size;
  $('info-skins').textContent = skinCount;
  $('bone-list').innerHTML = bones.map(name => '<span>' + escapeHtml(name) + '</span>').join('') || 'No bones found.';
  $('animation-list').innerHTML = Array.from(actions.keys()).map(name => '<span>' + escapeHtml(name) + '</span>').join('') || 'No clips found.';
}
function enableControls() {
  ['play-pause','stop-animation','speed-select','clip-select','timeline','autonomy-toggle'].forEach(id => { $(id).disabled = false; });
  document.querySelectorAll('#quick-actions button').forEach(button => { button.disabled = !actions.has(button.dataset.clip); });
  $('autonomy-toggle').checked = false;
  setAutonomy(false);
}
async function loadModel(file) {
  initRenderer();
  setStatus('LOADING MODEL');
  $('empty-state').style.display = 'none';
  if (currentFileUrl) URL.revokeObjectURL(currentFileUrl);
  currentFileUrl = URL.createObjectURL(file);
  disposeModel();
  try {
    const loader = new GLTFLoader();
    const gltf = await loader.loadAsync(currentFileUrl);
    modelRoot = gltf.scene;
    scene.add(modelRoot);
    const bounds = new THREE.Box3().setFromObject(modelRoot);
    const size = bounds.getSize(new THREE.Vector3());
    const center = bounds.getCenter(new THREE.Vector3());
    modelRoot.position.x -= center.x;
    modelRoot.position.z -= center.z;
    modelRoot.position.y -= bounds.min.y;
    const maxDimension = Math.max(size.x, size.y, size.z);
    camera.position.set(0, Math.max(size.y * 0.55, 0.5), maxDimension * 2.8);
    orbit.target.set(0, size.y * 0.48, 0);
    orbit.update();
    mixer = new THREE.AnimationMixer(modelRoot);
    actions = new Map(gltf.animations.map(clip => [clip.name, mixer.clipAction(clip)]));
    morphEntries = collectMorphTargets(modelRoot);
    buildDiagnostics();
    renderMorphControls();
    const select = $('clip-select');
    select.innerHTML = '';
    gltf.animations.forEach(clip => {
      const option = document.createElement('option');
      option.value = clip.name;
      option.textContent = clip.name.replaceAll('_', ' ');
      select.append(option);
    });
    enableControls();
    $('model-label').textContent = file.name.toUpperCase();
    $('model-meta').textContent = bonesSummary() + ' bones · ' + gltf.animations.length + ' animation clips · ' + morphEntries.length + ' morph targets';
    $('clip-count').textContent = gltf.animations.length + ' CLIPS';
    setStatus('MODEL READY', true);
    if (actions.has('idle')) playClip('idle', { loop: true });
    else if (gltf.animations.length) playClip(gltf.animations[0].name, { loop: true });
  } catch (error) {
    console.error(error);
    setStatus('MODEL LOAD FAILED');
    $('empty-state').style.display = 'flex';
    $('empty-state').querySelector('h2').textContent = 'Could not load this model';
    $('empty-state').querySelector('p').textContent = error.message || 'Check that the file is a valid GLB.';
  }
}
function bonesSummary() {
  let count = 0;
  modelRoot.traverse(obj => { if (obj.isBone) count++; });
  return count;
}

$('model-file').addEventListener('change', event => {
  const file = event.target.files && event.target.files[0];
  if (file) loadModel(file);
  event.target.value = '';
});
stage.addEventListener('dragover', event => { event.preventDefault(); stage.classList.add('dragging'); });
stage.addEventListener('dragleave', () => stage.classList.remove('dragging'));
stage.addEventListener('drop', event => {
  event.preventDefault();
  stage.classList.remove('dragging');
  const file = Array.from(event.dataTransfer.files).find(item => /\.glb$|\.gltf$/i.test(item.name));
  if (file) loadModel(file);
});
$('clip-select').addEventListener('change', event => {
  setAutonomy(false); $('autonomy-toggle').checked = false;
  playClip(event.target.value, { loop: false });
});
$('play-pause').addEventListener('click', () => {
  if (!activeAction) playClip($('clip-select').value, { loop: true });
  else if (activeAction.paused) {
    activeAction.paused = false;
    $('play-pause').innerHTML = 'Ⅱ <span>Pause</span>';
  } else {
    activeAction.paused = true;
    $('play-pause').innerHTML = '▶ <span>Resume</span>';
  }
});
$('stop-animation').addEventListener('click', stopPlayback);
$('speed-select').addEventListener('change', event => {
  if (activeAction) activeAction.setEffectiveTimeScale(Number(event.target.value));
});
$('timeline').addEventListener('input', event => {
  if (!activeAction) return;
  activeAction.paused = true;
  activeAction.time = Number(event.target.value) * activeAction.getClip().duration;
  mixer.update(0);
  $('play-pause').innerHTML = '▶ <span>Resume</span>';
});
$('autonomy-toggle').addEventListener('change', event => setAutonomy(event.target.checked));
document.querySelectorAll('[data-clip]').forEach(button => button.addEventListener('click', () => {
  setAutonomy(false); $('autonomy-toggle').checked = false;
  playClip(button.dataset.clip, { loop: false });
}));
document.querySelectorAll('[data-face]').forEach(button => button.addEventListener('click', () => setFacePreset(button.dataset.face)));
$('reset-face').addEventListener('click', () => { resetMorphs(); renderMorphControls(); });
document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.tab,.tab-content').forEach(element => element.classList.remove('active'));
  button.classList.add('active');
  $('tab-' + button.dataset.tab).classList.add('active');
}));
$('reset-camera').addEventListener('click', () => {
  if (!modelRoot) return;
  const bounds = new THREE.Box3().setFromObject(modelRoot);
  const size = bounds.getSize(new THREE.Vector3());
  camera.position.set(0, size.y * 0.55, Math.max(size.x, size.y, size.z) * 2.8);
  orbit.target.set(0, size.y * 0.48, 0);
  orbit.update();
});
$('fullscreen').addEventListener('click', () => { if (stage.requestFullscreen) stage.requestFullscreen(); });
initRenderer();
setStatus('WAITING FOR MODEL');
