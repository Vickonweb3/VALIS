package ai.valis.character.pose

import kotlin.math.floor
import kotlin.math.min

/** Rest (bind) pose of every pack joint, read from the model once at load. */
class RestPose(val rotation: FloatArray, val translation: FloatArray, val scale: FloatArray) {
    init {
        require(rotation.size % 4 == 0 && translation.size == rotation.size / 4 * 3 && scale.size == translation.size) { "inconsistent rest pose" }
    }
    val jointCount get() = rotation.size / 4
}

/** The pose handed to the renderer each frame. Buffers are reused; read them, do not keep them. */
class Pose(jointCount: Int, morphCounts: Map<String, Int>) {
    val rotation = FloatArray(jointCount * 4)
    val translation = FloatArray(jointCount * 3)
    val scale = FloatArray(jointCount * 3)
    val morphs: Map<String, FloatArray> = morphCounts.mapValues { FloatArray(it.value) }
}

/**
 * Animation layers, composed bottom-up. A layer owns the joints in [jointMask] (null = all)
 * and the morph groups in [morphGroups] (null = all); a higher layer blends over lower ones by its weight.
 */
enum class Layer(val order: Int) { BASE(0), GESTURE(1), FACE(2) }

/**
 * Samples baked clips and composes layers into a [Pose]. Pure computation: no engine types,
 * no allocation per frame after construction, deterministic for a given sequence of calls.
 */
class PoseRuntime(
    private val pack: AnimationPack,
    private val rest: RestPose,
    morphCounts: Map<String, Int>,
) {
    init { require(rest.jointCount == pack.joints.size) { "rest pose has ${rest.jointCount} joints, pack has ${pack.joints.size}" } }

    private class Playback(val clip: Clip, val loop: Boolean) {
        var time = 0f
        var finished = false
    }

    private class Slot(val layer: Layer) {
        var current: Playback? = null
        var previous: Playback? = null
        var fade = 1f          // 0..1 progress from previous to current
        var fadeRate = 0f      // per second
        var weight = 1f
        var jointMask: BooleanArray? = null
        var morphGroups: Set<String>? = null
    }

    private val slots = Layer.entries.associateWith { Slot(it) }
    private val ordered = Layer.entries.sortedBy { it.order }
    val pose = Pose(rest.jointCount, morphCounts)
    private val morphOverrides = HashMap<String, FloatArray>()  // mesh -> NaN = not overridden

    private val tmpA = Pose(rest.jointCount, morphCounts)
    private val tmpB = Pose(rest.jointCount, morphCounts)
    private val scratch = FloatArray(4)
    private val morphCountsCopy = morphCounts

    init { reset() }

    fun reset() {
        System.arraycopy(rest.rotation, 0, pose.rotation, 0, rest.rotation.size)
        System.arraycopy(rest.translation, 0, pose.translation, 0, rest.translation.size)
        System.arraycopy(rest.scale, 0, pose.scale, 0, rest.scale.size)
        pose.morphs.values.forEach { it.fill(0f) }
    }

    /**
     * Starts [clipName] on [layer], crossfading from whatever played before.
     * Returns false (and changes nothing) when the clip does not exist.
     */
    fun play(layer: Layer, clipName: String, loop: Boolean, fadeSeconds: Float = 0.25f, mask: IntArray? = null, groups: Set<String>? = null): Boolean {
        val clip = pack.clip(clipName) ?: return false
        val s = slots.getValue(layer)
        s.previous = s.current
        s.current = Playback(clip, loop)
        s.fade = if (s.previous == null || fadeSeconds <= 0f) 1f else 0f
        s.fadeRate = if (fadeSeconds <= 0f) 0f else 1f / fadeSeconds
        s.jointMask = mask?.let { m -> BooleanArray(rest.jointCount).also { b -> m.forEach { j -> b[j] = true } } }
        s.morphGroups = groups
        return true
    }

    fun stop(layer: Layer, fadeSeconds: Float = 0.25f) {
        val s = slots.getValue(layer)
        s.previous = s.current
        s.current = null
        s.fade = if (fadeSeconds <= 0f) 1f else 0f
        s.fadeRate = if (fadeSeconds <= 0f) 0f else 1f / fadeSeconds
    }

    fun setLayerWeight(layer: Layer, weight: Float) { slots.getValue(layer).weight = weight.coerceIn(0f, 1f) }

    /** Procedural override applied after all clips (speech visemes, blinks). Pass NaN-free weight in 0..1. */
    fun setMorphOverride(mesh: String, target: Int, weight: Float) {
        val count = morphCountsCopy[mesh] ?: return
        if (target !in 0 until count) return
        morphOverrides.getOrPut(mesh) { FloatArray(count) { Float.NaN } }[target] = weight.coerceIn(0f, 1f)
    }

    fun clearMorphOverride(mesh: String, target: Int) { morphOverrides[mesh]?.let { if (target in it.indices) it[target] = Float.NaN } }

    fun isFinished(layer: Layer): Boolean = slots.getValue(layer).current?.finished ?: true

    /** Advances all layers by [dt] seconds and recomposes [pose]. */
    fun update(dt: Float): Pose {
        val step = dt.coerceIn(0f, 0.1f)  // a stalled frame must not teleport the animation
        reset()
        for (layer in ordered) {
            val s = slots.getValue(layer)
            advance(s.current, step)
            advance(s.previous, step)
            if (s.fade < 1f) s.fade = min(1f, s.fade + s.fadeRate * step)
            if (s.fade >= 1f) s.previous = null
            if (s.current == null && s.previous == null) continue
            compose(s)
        }
        applyOverrides()
        return pose
    }

    private fun advance(p: Playback?, dt: Float) {
        p ?: return
        if (p.finished) return
        p.time += dt
        if (p.time >= p.clip.duration) {
            if (p.loop && p.clip.duration > 0f) p.time %= p.clip.duration
            else { p.time = p.clip.duration; p.finished = true }
        }
    }

    private fun compose(s: Slot) {
        val cur = s.current
        val prev = s.previous
        // Sample into tmpA (target) and, while fading, tmpB (source); blend into tmpA.
        tmpA.let { seedFromPose(it) }
        if (cur != null) sample(cur, tmpA)
        if (prev != null && s.fade < 1f) {
            seedFromPose(tmpB)
            sample(prev, tmpB)
            blend(tmpB, tmpA, s.fade, tmpA, null, null)
        }
        blend(pose, tmpA, s.weight, pose, s.jointMask, s.morphGroups)
    }

    private fun seedFromPose(into: Pose) {
        System.arraycopy(pose.rotation, 0, into.rotation, 0, pose.rotation.size)
        System.arraycopy(pose.translation, 0, into.translation, 0, pose.translation.size)
        System.arraycopy(pose.scale, 0, into.scale, 0, pose.scale.size)
        for ((m, a) in pose.morphs) System.arraycopy(a, 0, into.morphs.getValue(m), 0, a.size)
    }

    private fun sample(p: Playback, out: Pose) {
        val clip = p.clip
        val fpos = (p.time * pack.fps).coerceIn(0f, (clip.frames - 1).toFloat())
        val f0 = floor(fpos).toInt().coerceAtMost(clip.frames - 2)
        val t = fpos - f0
        for (jt in clip.joints) {
            val j = jt.joint
            pack.rotation(jt.rotation, f0, scratch0, 0)
            pack.rotation(jt.rotation, f0 + 1, scratch0, 4)
            Quat.nlerp(scratch0, 0, scratch0, 4, t, out.rotation, j * 4)
            jt.translation?.let {
                pack.vec3(it, f0, scratch0, 0); pack.vec3(it, f0 + 1, scratch0, 3)
                for (i in 0 until 3) out.translation[j * 3 + i] = scratch0[i] * (1 - t) + scratch0[3 + i] * t
            }
            jt.scale?.let {
                pack.vec3(it, f0, scratch0, 0); pack.vec3(it, f0 + 1, scratch0, 3)
                for (i in 0 until 3) out.scale[j * 3 + i] = scratch0[i] * (1 - t) + scratch0[3 + i] * t
            }
        }
        for (mt in clip.morphs) {
            val dst = out.morphs[mt.mesh] ?: continue
            val cols = mt.targets.size
            for (c in 0 until cols) {
                val w0 = pack.weight(mt.weights, f0, c, cols)
                val w1 = pack.weight(mt.weights, f0 + 1, c, cols)
                dst[mt.targets[c]] = w0 * (1 - t) + w1 * t
            }
        }
    }
    private val scratch0 = FloatArray(8)

    /** out = lerp(a, b, w), restricted to the masked joints and morph groups; unmasked channels copy `a`. */
    private fun blend(a: Pose, b: Pose, w: Float, out: Pose, jointMask: BooleanArray?, groups: Set<String>?) {
        for (j in 0 until rest.jointCount) {
            val on = jointMask == null || jointMask[j]
            val k = if (on) w else 0f
            Quat.nlerp(a.rotation, j * 4, b.rotation, j * 4, k, out.rotation, j * 4)
            for (i in 0 until 3) {
                out.translation[j * 3 + i] = a.translation[j * 3 + i] * (1 - k) + b.translation[j * 3 + i] * k
                out.scale[j * 3 + i] = a.scale[j * 3 + i] * (1 - k) + b.scale[j * 3 + i] * k
            }
        }
        for ((mesh, dst) in out.morphs) {
            val av = a.morphs.getValue(mesh); val bv = b.morphs.getValue(mesh)
            for (i in dst.indices) {
                val on = groups == null || groupOf(mesh, i)?.let { it in groups } == true
                val k = if (on) w else 0f
                dst[i] = av[i] * (1 - k) + bv[i] * k
            }
        }
    }

    // target -> group, learned from the clips themselves so the runtime never hard-codes morph names.
    private val groupIndex: Map<String, Array<String?>> by lazy {
        val m = HashMap<String, Array<String?>>()
        for ((mesh, count) in morphCountsCopy) m[mesh] = arrayOfNulls(count)
        for (clip in pack.clips) for (mt in clip.morphs) for (t in mt.targets) m[mt.mesh]?.set(t, mt.group)
        m
    }
    private fun groupOf(mesh: String, target: Int): String? = groupIndex[mesh]?.get(target)

    private fun applyOverrides() {
        for ((mesh, ov) in morphOverrides) {
            val dst = pose.morphs[mesh] ?: continue
            for (i in ov.indices) if (!ov[i].isNaN()) dst[i] = ov[i]
        }
    }
}
