package ai.valis.character.pose

import kotlin.math.sqrt

/** Column-major 4x4 transforms (Filament's layout) from/to translation, rotation (xyzw) and scale. */
object Trs {
    fun compose(t: FloatArray, ti: Int, q: FloatArray, qi: Int, s: FloatArray, si: Int, m: FloatArray) {
        val x = q[qi]; val y = q[qi + 1]; val z = q[qi + 2]; val w = q[qi + 3]
        val xx = x * x; val yy = y * y; val zz = z * z
        val xy = x * y; val xz = x * z; val yz = y * z
        val wx = w * x; val wy = w * y; val wz = w * z
        val sx = s[si]; val sy = s[si + 1]; val sz = s[si + 2]
        m[0] = (1 - 2 * (yy + zz)) * sx; m[1] = 2 * (xy + wz) * sx;       m[2] = 2 * (xz - wy) * sx;       m[3] = 0f
        m[4] = 2 * (xy - wz) * sy;       m[5] = (1 - 2 * (xx + zz)) * sy; m[6] = 2 * (yz + wx) * sy;       m[7] = 0f
        m[8] = 2 * (xz + wy) * sz;       m[9] = 2 * (yz - wx) * sz;       m[10] = (1 - 2 * (xx + yy)) * sz; m[11] = 0f
        m[12] = t[ti]; m[13] = t[ti + 1]; m[14] = t[ti + 2]; m[15] = 1f
    }

    /** Inverse of [compose] for matrices without shear or negative scale (true for glTF node transforms here). */
    fun decompose(m: FloatArray, t: FloatArray, ti: Int, q: FloatArray, qi: Int, s: FloatArray, si: Int) {
        t[ti] = m[12]; t[ti + 1] = m[13]; t[ti + 2] = m[14]
        val sx = len(m[0], m[1], m[2]); val sy = len(m[4], m[5], m[6]); val sz = len(m[8], m[9], m[10])
        s[si] = sx; s[si + 1] = sy; s[si + 2] = sz
        val r00 = m[0] / sx; val r10 = m[1] / sx; val r20 = m[2] / sx
        val r01 = m[4] / sy; val r11 = m[5] / sy; val r21 = m[6] / sy
        val r02 = m[8] / sz; val r12 = m[9] / sz; val r22 = m[10] / sz
        val tr = r00 + r11 + r22
        val x: Float; val y: Float; val z: Float; val w: Float
        if (tr > 0f) {
            val k = sqrt(tr + 1f) * 2f
            w = 0.25f * k; x = (r21 - r12) / k; y = (r02 - r20) / k; z = (r10 - r01) / k
        } else if (r00 > r11 && r00 > r22) {
            val k = sqrt(1f + r00 - r11 - r22) * 2f
            w = (r21 - r12) / k; x = 0.25f * k; y = (r01 + r10) / k; z = (r02 + r20) / k
        } else if (r11 > r22) {
            val k = sqrt(1f + r11 - r00 - r22) * 2f
            w = (r02 - r20) / k; x = (r01 + r10) / k; y = 0.25f * k; z = (r12 + r21) / k
        } else {
            val k = sqrt(1f + r22 - r00 - r11) * 2f
            w = (r10 - r01) / k; x = (r02 + r20) / k; y = (r12 + r21) / k; z = 0.25f * k
        }
        q[qi] = x; q[qi + 1] = y; q[qi + 2] = z; q[qi + 3] = w
        Quat.normalize(q, qi)
    }

    private fun len(a: Float, b: Float, c: Float) = sqrt(a * a + b * b + c * c).coerceAtLeast(1e-8f)
}
