package ai.valis.character.pose

import ai.valis.character.CharacterState
import org.junit.Assert.*
import org.junit.Test

class TrsAndPlanTest {
    @Test fun composeDecomposeRoundTrips() {
        val q = floatArrayOf(0.2f, -0.4f, 0.5f, 0.7f).also { Quat.normalize(it, 0) }
        val t = floatArrayOf(1f, -2f, 3f); val s = floatArrayOf(1.5f, 0.5f, 2f)
        val m = FloatArray(16); Trs.compose(t, 0, q, 0, s, 0, m)
        val t2 = FloatArray(3); val q2 = FloatArray(4); val s2 = FloatArray(3)
        Trs.decompose(m, t2, 0, q2, 0, s2, 0)
        assertArrayEquals(t, t2, 1e-5f); assertArrayEquals(s, s2, 1e-5f)
        val sign = if (q[3] * q2[3] < 0) -1f else 1f
        for (i in 0 until 4) assertEquals(q[i], q2[i] * sign, 1e-4f)
    }

    @Test fun identityComposesToIdentityMatrix() {
        val m = FloatArray(16)
        Trs.compose(FloatArray(3), 0, floatArrayOf(0f, 0f, 0f, 1f), 0, floatArrayOf(1f, 1f, 1f), 0, m)
        for (i in 0 until 16) assertEquals(if (i % 5 == 0) 1f else 0f, m[i], 1e-6f)
    }

    @Test fun decomposeCoversEveryQuaternionBranch() {
        for (axis in 0..2) for (deg in listOf(10.0, 100.0, 170.0)) {
            val h = Math.toRadians(deg) / 2
            val q = FloatArray(4); q[axis] = Math.sin(h).toFloat(); q[3] = Math.cos(h).toFloat()
            val m = FloatArray(16); Trs.compose(FloatArray(3), 0, q, 0, floatArrayOf(1f, 1f, 1f), 0, m)
            val q2 = FloatArray(4); Trs.decompose(m, FloatArray(3), 0, q2, 0, FloatArray(3), 0)
            val sign = if (q[3] * q2[3] < 0) -1f else 1f
            for (i in 0 until 4) assertEquals("axis $axis deg $deg", q[i], q2[i] * sign, 1e-4f)
        }
    }

    @Test fun everyStateHasAPlanAndOnlyDormantIsEmpty() {
        for (s in CharacterState.entries) {
            val p = StatePlans.of(s)
            if (s == CharacterState.DORMANT) assertNull(p.base) else assertNotNull("$s", p.base)
        }
    }

    @Test fun speakingOwnsOnlyMouthGroups() {
        assertEquals(setOf("MOUTH", "VISEME"), StatePlans.of(CharacterState.SPEAKING).faceGroups)
    }

    @Test fun missingClipsAreSkippedNotFatal() {
        val b = PoseTestSupport.build()   // contains only "wave"
        val pack = AnimationPack.parse(b.json, b.payload)
        val rt = PoseRuntime(pack, PoseTestSupport.rest(), mapOf("face" to 2))
        for (s in CharacterState.entries) StatePlans.apply(rt, pack, s)
        rt.update(0.016f)
    }
}
