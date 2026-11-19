package ai.valis.character.pose

import kotlin.math.sqrt

/** Quaternion helpers over flat xyzw FloatArrays, allocation-free so they are safe in the render loop. */
internal object Quat {
    fun normalize(a: FloatArray, at: Int) {
        val n = sqrt(a[at] * a[at] + a[at + 1] * a[at + 1] + a[at + 2] * a[at + 2] + a[at + 3] * a[at + 3])
        if (n < 1e-8f) { a[at] = 0f; a[at + 1] = 0f; a[at + 2] = 0f; a[at + 3] = 1f; return }
        val inv = 1f / n
        for (i in 0 until 4) a[at + i] *= inv
    }

    /** Normalised lerp along the shortest arc: out = nlerp(a, b, t). `out` may alias `a`. */
    fun nlerp(a: FloatArray, ai: Int, b: FloatArray, bi: Int, t: Float, out: FloatArray, oi: Int) {
        val dot = a[ai] * b[bi] + a[ai + 1] * b[bi + 1] + a[ai + 2] * b[bi + 2] + a[ai + 3] * b[bi + 3]
        val s = if (dot < 0f) -1f else 1f
        for (i in 0 until 4) out[oi + i] = a[ai + i] * (1f - t) + b[bi + i] * t * s
        normalize(out, oi)
    }
}
