package ai.valis.character.pose

import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Builds a tiny valis_anim.v1 pack in memory: joints root/arm, one mesh "face" with morphs blink/smile. */
internal object PoseTestSupport {
    class Built(val json: String, val payload: ByteArray)

    private fun q(deg: Double): ShortArray {
        val h = Math.toRadians(deg) / 2
        return shortArrayOf(0, 0, (Math.sin(h) * 32767).toInt().toShort(), (Math.cos(h) * 32767).toInt().toShort())
    }

    /** arm rotates 0 -> [armDegEnd] about Z over [frames] frames; smile goes 0 -> 1. */
    fun build(armDegEnd: Double = 90.0, frames: Int = 31, loopable: Boolean = false, extraClip: Boolean = false): Built {
        val out = ByteArrayOutputStream()
        fun align() { while (out.size() % 4 != 0) out.write(0) }
        fun rotations(endDeg: Double): Int {
            align(); val off = out.size()
            val bb = ByteBuffer.allocate(frames * 8).order(ByteOrder.LITTLE_ENDIAN)
            for (f in 0 until frames) q(endDeg * f / (frames - 1)).forEach { bb.putShort(it) }
            out.write(bb.array()); return off
        }
        fun weights(): Int {
            align(); val off = out.size()
            val bb = ByteBuffer.allocate(frames * 2).order(ByteOrder.LITTLE_ENDIAN)
            for (f in 0 until frames) bb.putShort((65535 * f / (frames - 1)).toShort())
            out.write(bb.array()); return off
        }
        val rOff = rotations(armDegEnd); val wOff = weights()
        val rOff2 = if (extraClip) rotations(-armDegEnd) else 0
        fun clip(name: String, r: Int) = """{"name":"$name","duration":1.0,"frames":$frames,"loopable":$loopable,"loopErrorDeg":0,
          "movingJoints":[1],"meaningfulMask":[1],
          "joints":[{"joint":1,"rotation":{"offset":$r,"count":${frames * 4}},"rangeDeg":$armDegEnd}],
          "morphs":[{"mesh":"face","group":"MOUTH","targets":[1],"weights":{"offset":$wOff,"count":$frames}}]}"""
        val clips = clip("wave", rOff) + if (extraClip) "," + clip("reverse", rOff2) else ""
        val json = """{"format":"valis_anim.v1","fps":30,"joints":["root","arm"],"morphs":{"face":["blink","smile"]},
          "groups":["MOUTH"],"encoding":{},"clips":[$clips]}"""
        return Built(json, out.toByteArray())
    }

    fun rest() = RestPose(
        floatArrayOf(0f, 0f, 0f, 1f, 0f, 0f, 0f, 1f),
        FloatArray(6), floatArrayOf(1f, 1f, 1f, 1f, 1f, 1f),
    )

    fun angleZDeg(q: FloatArray, joint: Int): Double =
        Math.toDegrees(2 * Math.atan2(q[joint * 4 + 2].toDouble(), q[joint * 4 + 3].toDouble()))
}
