package ai.valis.character.pose

import org.json.JSONArray
import org.json.JSONObject
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Thrown when a baked animation pack is malformed. The renderer refuses to start on it. */
class PackFormatException(message: String) : IllegalArgumentException(message)

/** A float/int16/uint16 array inside the pack payload, addressed by byte offset and element count. */
class ArrayRef(val offset: Int, val count: Int)

class JointTrack(
    val joint: Int,
    val rotation: ArrayRef,
    val translation: ArrayRef?,
    val scale: ArrayRef?,
)

class MorphTrack(
    val mesh: String,
    val group: String,
    /** Indices into the mesh's morph target list; weights are stored frame-major over these. */
    val targets: IntArray,
    val weights: ArrayRef,
)

class Clip(
    val name: String,
    val duration: Float,
    val frames: Int,
    val loopable: Boolean,
    val meaningfulMask: IntArray,
    val joints: List<JointTrack>,
    val morphs: List<MorphTrack>,
)

/**
 * The runtime form of `valis_anim.v1` produced by tools/asset-pipeline.
 * Validated eagerly: a bad offset here would otherwise surface as a crash mid-animation.
 */
class AnimationPack private constructor(
    val fps: Int,
    val joints: List<String>,
    /** mesh node name -> ordered morph target names */
    val morphs: Map<String, List<String>>,
    val clips: List<Clip>,
    private val payload: ByteBuffer,
) {
    private val byName = clips.associateBy { it.name }

    fun clip(name: String): Clip? = byName[name]

    fun rotation(ref: ArrayRef, frame: Int, out: FloatArray, at: Int) {
        val base = ref.offset + frame * 8
        for (i in 0 until 4) out[at + i] = payload.getShort(base + i * 2) / 32767f
        Quat.normalize(out, at)
    }

    fun vec3(ref: ArrayRef, frame: Int, out: FloatArray, at: Int) {
        val base = ref.offset + frame * 12
        for (i in 0 until 3) out[at + i] = payload.getFloat(base + i * 4)
    }

    fun weight(ref: ArrayRef, frame: Int, column: Int, columns: Int): Float =
        (payload.getShort(ref.offset + (frame * columns + column) * 2).toInt() and 0xFFFF) / 65535f

    companion object {
        const val FORMAT = "valis_anim.v1"

        fun parse(indexJson: String, payload: ByteArray): AnimationPack {
            val root = try { JSONObject(indexJson) } catch (e: Exception) { throw PackFormatException("index is not valid JSON: ${e.message}") }
            if (root.optString("format") != FORMAT) throw PackFormatException("unsupported format '${root.optString("format")}'")
            val buf = ByteBuffer.wrap(payload).order(ByteOrder.LITTLE_ENDIAN)
            val joints = strings(root.getJSONArray("joints"))
            val morphObj = root.getJSONObject("morphs")
            val morphs = LinkedHashMap<String, List<String>>()
            for (k in morphObj.keys()) morphs[k] = strings(morphObj.getJSONArray(k))

            fun ref(o: JSONObject, bytesPerElement: Int, elementsPerFrame: Int, frames: Int, what: String): ArrayRef {
                val r = ArrayRef(o.getInt("offset"), o.getInt("count"))
                if (r.count != elementsPerFrame * frames) throw PackFormatException("$what: count ${r.count} != $elementsPerFrame x $frames")
                if (r.offset < 0 || r.offset.toLong() + r.count.toLong() * bytesPerElement > payload.size)
                    throw PackFormatException("$what: range exceeds payload")
                return r
            }

            val clips = ArrayList<Clip>()
            val clipArr = root.getJSONArray("clips")
            for (ci in 0 until clipArr.length()) {
                val c = clipArr.getJSONObject(ci)
                val name = c.getString("name")
                val frames = c.getInt("frames")
                if (frames < 2) throw PackFormatException("clip '$name' has fewer than 2 frames")
                val jt = ArrayList<JointTrack>()
                val ja = c.getJSONArray("joints")
                for (i in 0 until ja.length()) {
                    val j = ja.getJSONObject(i)
                    val ji = j.getInt("joint")
                    if (ji !in joints.indices) throw PackFormatException("clip '$name': joint index $ji out of range")
                    jt += JointTrack(
                        ji,
                        ref(j.getJSONObject("rotation"), 2, 4, frames, "$name/rotation"),
                        j.optJSONObject("translation")?.let { ref(it, 4, 3, frames, "$name/translation") },
                        j.optJSONObject("scale")?.let { ref(it, 4, 3, frames, "$name/scale") },
                    )
                }
                val mt = ArrayList<MorphTrack>()
                val ma = c.getJSONArray("morphs")
                for (i in 0 until ma.length()) {
                    val m = ma.getJSONObject(i)
                    val mesh = m.getString("mesh")
                    val names = morphs[mesh] ?: throw PackFormatException("clip '$name': unknown mesh '$mesh'")
                    val targets = ints(m.getJSONArray("targets"))
                    if (targets.any { it !in names.indices }) throw PackFormatException("clip '$name': morph target out of range on '$mesh'")
                    mt += MorphTrack(mesh, m.getString("group"), targets,
                        ref(m.getJSONObject("weights"), 2, targets.size, frames, "$name/weights"))
                }
                clips += Clip(name, c.getDouble("duration").toFloat(), frames, c.getBoolean("loopable"),
                    ints(c.getJSONArray("meaningfulMask")), jt, mt)
            }
            return AnimationPack(root.getInt("fps"), joints, morphs, clips, buf)
        }

        private fun strings(a: JSONArray) = List(a.length()) { a.getString(it) }
        private fun ints(a: JSONArray) = IntArray(a.length()) { a.getInt(it) }
    }
}
