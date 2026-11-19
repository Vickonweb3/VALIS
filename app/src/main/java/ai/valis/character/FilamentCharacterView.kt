package ai.valis.character

import android.content.Context
import android.graphics.PixelFormat
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.Choreographer
import android.view.SurfaceView
import android.widget.FrameLayout
import ai.valis.character.pose.AnimationPack
import ai.valis.character.pose.Layer
import ai.valis.character.pose.PoseRuntime
import ai.valis.character.pose.RestPose
import ai.valis.character.pose.Rig
import ai.valis.character.pose.RigBinder
import ai.valis.character.pose.StatePlans
import ai.valis.character.pose.Trs
import com.google.android.filament.Camera
import com.google.android.filament.Engine
import com.google.android.filament.EntityManager
import com.google.android.filament.IndirectLight
import com.google.android.filament.LightManager
import com.google.android.filament.Renderer
import com.google.android.filament.Scene
import com.google.android.filament.SwapChain
import com.google.android.filament.View
import com.google.android.filament.Viewport
import com.google.android.filament.android.UiHelper
import com.google.android.filament.gltfio.AssetLoader
import com.google.android.filament.gltfio.FilamentAsset
import com.google.android.filament.gltfio.ResourceLoader
import com.google.android.filament.gltfio.UbershaderProvider
import java.nio.ByteBuffer
import kotlin.math.max
import kotlin.math.tan

/**
 * Renders the VALIS character on a transparent surface.
 *
 * Threading: every Filament call happens on the main thread. Only asset bytes are read off-thread.
 * Failure policy: a missing or mismatched asset is reported through [onError] and nothing is drawn;
 * the host shows its fallback. The view never throws from a lifecycle callback.
 */
class FilamentCharacterView(context: Context) : FrameLayout(context) {
    private val main = Handler(Looper.getMainLooper())
    private val surface = SurfaceView(context).apply {
        setZOrderOnTop(true)
        holder.setFormat(PixelFormat.TRANSLUCENT)
    }
    private val ui = UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK).apply { isOpaque = false }

    private var engine: Engine? = null
    private var renderer: Renderer? = null
    private var scene: Scene? = null
    private var view: View? = null
    private var camera: Camera? = null
    private var cameraEntity = 0
    private var sun = 0
    private var ibl: IndirectLight? = null
    private var swapChain: SwapChain? = null
    private var nativeSurface: android.view.Surface? = null
    private var provider: UbershaderProvider? = null
    private var loader: AssetLoader? = null
    private var asset: FilamentAsset? = null

    private var pack: AnimationPack? = null
    private var rig: Rig? = null
    private var runtime: PoseRuntime? = null
    private var pendingState: CharacterState = CharacterState.IDLE
    private val matrix = FloatArray(16)

    private var running = false
    private var lastFrameNanos = 0L
    private var destroyed = false
    private var firstFrameLogged = false
    var onError: (Throwable) -> Unit = { Log.e(TAG, "character failed", it) }
    var onReady: () -> Unit = {}

    init {
        addView(surface, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        ui.renderCallback = object : UiHelper.RendererCallback {
            override fun onNativeWindowChanged(s: android.view.Surface) {
                nativeSurface = s   // remembered: the surface usually arrives before the model finishes loading
                val e = engine ?: return
                swapChain?.let { e.destroySwapChain(it) }
                swapChain = e.createSwapChain(s, ui.swapChainFlags)
            }
            override fun onDetachedFromSurface() {
                nativeSurface = null
                val e = engine ?: return
                swapChain?.let { e.destroySwapChain(it); e.flushAndWait() }
                swapChain = null
            }
            override fun onResized(width: Int, height: Int) { resize(width, height) }
        }
        ui.attachTo(surface)
    }

    /** Loads the model and its baked animation pack from assets. [modelAsset] falls back to the full-quality GLB. */
    fun load(modelAssets: List<String> = listOf("valis/VALIS_runtime.glb", "valis/VALIS_rigged.glb"),
             packAsset: String = "valis/valis_anim.v1") {
        Thread({
            try {
                val glb = modelAssets.firstNotNullOfOrNull { n -> runCatching { context.assets.open(n).use { it.readBytes() } }.getOrNull() }
                    ?: error("No character model in assets (tried ${modelAssets.joinToString()}).")
                val index = context.assets.open("$packAsset.json").use { String(it.readBytes(), Charsets.UTF_8) }
                val payload = context.assets.open("$packAsset.bin").use { it.readBytes() }
                val parsed = AnimationPack.parse(index, payload)
                main.post { if (!destroyed) attach(glb, parsed) }
            } catch (t: Throwable) {
                main.post { if (!destroyed) onError(t) }
            }
        }, "valis-character-load").start()
    }

    private fun attach(glb: ByteArray, parsed: AnimationPack) {
        try {
            val e = Engine.create().also { engine = it }
            renderer = e.createRenderer().apply { clearOptions = Renderer.ClearOptions().apply { clear = true } }
            scene = e.createScene()
            cameraEntity = EntityManager.get().create()
            camera = e.createCamera(cameraEntity)
            view = e.createView().also {
                it.scene = scene; it.camera = camera
                it.blendMode = View.BlendMode.TRANSLUCENT
            }
            addLights(e)
            nativeSurface?.let { swapChain = e.createSwapChain(it, ui.swapChainFlags) }

            val p = UbershaderProvider(e).also { provider = it }
            val l = AssetLoader(e, p, EntityManager.get()).also { loader = it }
            val a = l.createAsset(ByteBuffer.wrap(glb)) ?: error("Model could not be parsed.")
            asset = a
            val rl = ResourceLoader(e)
            try { rl.loadResources(a) } finally { rl.destroy() }
            a.releaseSourceData()
            scene!!.addEntities(a.entities)

            val tm = e.transformManager
            val boundRig = RigBinder.bind(
                parsed,
                resolveNode = { name -> a.getFirstEntityByName(name).takeIf { it != 0 } },
                morphNames = { ent -> a.getMorphTargetNames(ent).toList() },
            )
            val rest = readRest(parsed, boundRig, tm)
            pack = parsed; rig = boundRig
            runtime = PoseRuntime(parsed, rest, boundRig.morphCounts)
            StatePlans.apply(runtime!!, parsed, pendingState)
            frameCamera(a)
            if (width > 0) resize(width, height)
            startLoop()
            Log.i(TAG, "character ready: ${parsed.joints.size} joints, ${parsed.clips.size} clips")
            onReady()
        } catch (t: Throwable) {
            releaseEngineObjects()
            onError(t)
        }
    }

    private fun addLights(e: Engine) {
        sun = EntityManager.get().create()
        LightManager.Builder(LightManager.Type.DIRECTIONAL)
            .color(1f, 0.98f, 0.95f).intensity(90_000f).direction(0.35f, -0.45f, -1f).castShadows(false)
            .build(e, sun)
        scene!!.addEntity(sun)
        ibl = IndirectLight.Builder().irradiance(1, floatArrayOf(0.55f, 0.58f, 0.7f)).intensity(30_000f).build(e)
        scene!!.indirectLight = ibl
    }

    private fun readRest(p: AnimationPack, r: Rig, tm: com.google.android.filament.TransformManager): RestPose {
        val n = p.joints.size
        val rot = FloatArray(n * 4); val pos = FloatArray(n * 3); val scl = FloatArray(n * 3)
        for (i in 0 until n) {
            val ti = tm.getInstance(r.jointEntities[i])
            tm.getTransform(ti, matrix)
            Trs.decompose(matrix, pos, i * 3, rot, i * 4, scl, i * 3)
        }
        return RestPose(rot, pos, scl)
    }

    /** Places the camera so the whole character fits the view height, looking slightly down at the chest. */
    private fun frameCamera(a: FilamentAsset) {
        val box = a.boundingBox
        val c = box.center; val h = box.halfExtent
        val radius = max(h[1], max(h[0], h[2]))
        val fov = 28.0
        val dist = (radius * 1.15 / tan(Math.toRadians(fov / 2))).toFloat()
        camera!!.lookAt(c[0].toDouble(), c[1].toDouble(), (c[2] + dist).toDouble(), c[0].toDouble(), c[1].toDouble(), c[2].toDouble(), 0.0, 1.0, 0.0)
        camNear = dist * 0.05f; camFar = dist * 4f
    }
    private var camNear = 0.1f
    private var camFar = 100f

    private fun resize(w: Int, h: Int) {
        if (w <= 0 || h <= 0) return
        view?.viewport = Viewport(0, 0, w, h)
        camera?.setProjection(28.0, w.toDouble() / h, camNear.toDouble(), camFar.toDouble(), Camera.Fov.VERTICAL)
    }

    fun setState(state: CharacterState) {
        pendingState = state
        val rt = runtime ?: return
        val pk = pack ?: return
        StatePlans.apply(rt, pk, state)
    }

    /** Direct speech control: visemes and blinks the speech layer drives each frame. */
    fun setMorphOverride(mesh: String, target: Int, weight: Float) { runtime?.setMorphOverride(mesh, target, weight) }
    fun clearMorphOverride(mesh: String, target: Int) { runtime?.clearMorphOverride(mesh, target) }
    fun playGesture(clip: String): Boolean {
        val rt = runtime ?: return false
        val mask = pack?.clip(clip)?.meaningfulMask
        return rt.play(Layer.GESTURE, clip, false, 0.2f, mask)
    }

    private val frame = object : Choreographer.FrameCallback {
        override fun doFrame(nanos: Long) {
            if (!running) return
            Choreographer.getInstance().postFrameCallback(this)
            val dt = if (lastFrameNanos == 0L) 0f else (nanos - lastFrameNanos) / 1e9f
            lastFrameNanos = nanos
            try { tick(dt, nanos) } catch (t: Throwable) { stopLoop(); onError(t) }
        }
    }

    private fun tick(dt: Float, nanos: Long) {
        val rt = runtime ?: return
        val r = rig ?: return
        val e = engine ?: return
        val pose = rt.update(dt)
        val tm = e.transformManager
        tm.openLocalTransformTransaction()
        for (i in r.jointEntities.indices) {
            Trs.compose(pose.translation, i * 3, pose.rotation, i * 4, pose.scale, i * 3, matrix)
            tm.setTransform(tm.getInstance(r.jointEntities[i]), matrix)
        }
        tm.commitLocalTransformTransaction()
        asset?.instance?.animator?.updateBoneMatrices()
        val rm = e.renderableManager
        for ((mesh, weights) in pose.morphs) {
            val ent = r.meshEntities[mesh] ?: continue
            val ri = rm.getInstance(ent)
            if (ri != 0) rm.setMorphWeights(ri, weights, 0)
        }
        val sc = swapChain ?: return
        val rd = renderer ?: return
        if (ui.isReadyToRender && rd.beginFrame(sc, nanos)) {
            rd.render(view!!); rd.endFrame()
            if (!firstFrameLogged) { firstFrameLogged = true; Log.i(TAG, "first frame rendered") }
        }
    }

    private fun startLoop() { if (!running && runtime != null) { running = true; lastFrameNanos = 0L; Choreographer.getInstance().postFrameCallback(frame) } }
    private fun stopLoop() { running = false; Choreographer.getInstance().removeFrameCallback(frame) }

    override fun onAttachedToWindow() { super.onAttachedToWindow(); startLoop() }
    override fun onDetachedFromWindow() { stopLoop(); super.onDetachedFromWindow() }

    /** Releases every GPU object. Safe to call twice. */
    fun destroy() {
        if (destroyed) return
        destroyed = true
        stopLoop()
        releaseEngineObjects()
        ui.detach()
    }

    private fun releaseEngineObjects() {
        val e = engine ?: return
        runtime = null; rig = null; pack = null
        asset?.let { loader?.destroyAsset(it) }; asset = null
        provider?.let { it.destroyMaterials(); it.destroy() }; provider = null
        loader?.destroy(); loader = null
        swapChain?.let { e.destroySwapChain(it) }; swapChain = null
        view?.let { e.destroyView(it) }; view = null
        scene?.let { e.destroyScene(it) }; scene = null
        ibl?.let { e.destroyIndirectLight(it) }; ibl = null
        if (sun != 0) { e.lightManager.destroy(sun); e.entityManager.destroy(sun); sun = 0 }
        camera?.let { e.destroyCameraComponent(cameraEntity); e.entityManager.destroy(cameraEntity) }; camera = null
        renderer?.let { e.destroyRenderer(it) }; renderer = null
        e.destroy(); engine = null
    }

    private companion object {
        const val TAG = "VALIS.Character"
        // Loads libfilament-jni and libgltfio-jni. Must run once before any Filament call.
        init {
            com.google.android.filament.Filament.init()
            com.google.android.filament.gltfio.Gltfio.init()
        }
    }
}
