package ai.valis.character.pose

import org.junit.Assert.*
import org.junit.Test

class PoseRuntimeTest {
    private fun runtime(extra: Boolean = false, loop: Boolean = false): Pair<AnimationPack, PoseRuntime> {
        val b = PoseTestSupport.build(extraClip = extra, loopable = loop)
        val pack = AnimationPack.parse(b.json, b.payload)
        return pack to PoseRuntime(pack, PoseTestSupport.rest(), mapOf("face" to 2))
    }

    @Test fun restPoseWhenNothingPlays() {
        val (_, rt) = runtime()
        val p = rt.update(0.016f)
        assertEquals(1f, p.rotation[3], 1e-6f)
        assertEquals(0f, p.morphs.getValue("face")[1], 1e-6f)
    }

    @Test fun samplesMidClipByInterpolation() {
        val (_, rt) = runtime()
        assertTrue(rt.play(Layer.BASE, "wave", loop = false, fadeSeconds = 0f))
        var p = rt.pose
        repeat(15) { p = rt.update(1f / 30) }   // 0.5 s of a 1 s, 0 -> 90 degree clip
        assertEquals(45.0, PoseTestSupport.angleZDeg(p.rotation, 1), 0.5)
        assertEquals(0.5f, p.morphs.getValue("face")[1], 0.02f)
        assertEquals("unanimated joint stays at rest", 0.0, PoseTestSupport.angleZDeg(p.rotation, 0), 1e-3)
    }

    @Test fun nonLoopingClipHoldsLastFrameAndReportsFinished() {
        val (_, rt) = runtime()
        rt.play(Layer.BASE, "wave", loop = false, fadeSeconds = 0f)
        repeat(60) { rt.update(1f / 30) }
        assertTrue(rt.isFinished(Layer.BASE))
        assertEquals(90.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 0.5)
    }

    @Test fun loopingClipWrapsAround() {
        val (_, rt) = runtime(loop = true)
        rt.play(Layer.BASE, "wave", loop = true, fadeSeconds = 0f)
        repeat(45) { rt.update(1f / 30) }   // 1.5 s -> 0.5 s into the second loop
        assertFalse(rt.isFinished(Layer.BASE))
        assertEquals(45.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 1.0)
    }

    @Test fun crossfadeBlendsBetweenClips() {
        val (_, rt) = runtime(extra = true)
        rt.play(Layer.BASE, "wave", loop = false, fadeSeconds = 0f)
        repeat(30) { rt.update(1f / 30) }                  // wave ends at +90
        rt.play(Layer.BASE, "reverse", loop = false, fadeSeconds = 0.5f)
        rt.update(0.0f)                                    // fade 0: still wave's pose
        assertEquals(90.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 1.0)
        repeat(10) { rt.update(1f / 30) }                  // two-thirds faded: wave held at 90, reverse at -30
        val mid = PoseTestSupport.angleZDeg(rt.pose.rotation, 1)
        assertTrue("blend should sit between the clips, was $mid", mid < 90.0 && mid > -30.0)
        repeat(30) { rt.update(1f / 30) }
        assertEquals(-90.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 1.0)
    }

    @Test fun jointMaskLeavesOtherJointsToLowerLayers() {
        val (_, rt) = runtime()
        rt.play(Layer.GESTURE, "wave", loop = false, fadeSeconds = 0f, mask = intArrayOf(0))  // mask excludes the arm
        repeat(30) { rt.update(1f / 30) }
        assertEquals(0.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 1e-3)
    }

    @Test fun morphGroupMaskBlocksUnownedGroups() {
        val (_, rt) = runtime()
        rt.play(Layer.GESTURE, "wave", loop = false, fadeSeconds = 0f, groups = setOf("BROW"))
        repeat(30) { rt.update(1f / 30) }
        assertEquals(0f, rt.pose.morphs.getValue("face")[1], 1e-6f)
        rt.play(Layer.GESTURE, "wave", loop = false, fadeSeconds = 0f, groups = setOf("MOUTH"))
        repeat(30) { rt.update(1f / 30) }
        assertEquals(1f, rt.pose.morphs.getValue("face")[1], 0.01f)
    }

    @Test fun morphOverrideWinsOverClips() {
        val (_, rt) = runtime()
        rt.play(Layer.BASE, "wave", loop = false, fadeSeconds = 0f)
        rt.setMorphOverride("face", 1, 0.2f)
        repeat(30) { rt.update(1f / 30) }
        assertEquals(0.2f, rt.pose.morphs.getValue("face")[1], 1e-6f)
        rt.clearMorphOverride("face", 1)
        rt.update(1f / 30)
        assertEquals(1f, rt.pose.morphs.getValue("face")[1], 0.01f)
    }

    @Test fun unknownClipIsRejectedWithoutSideEffects() {
        val (_, rt) = runtime()
        assertFalse(rt.play(Layer.BASE, "nope", loop = true))
        assertEquals(1f, rt.update(0.016f).rotation[7], 1e-6f)
    }

    @Test fun stalledFrameDoesNotTeleport() {
        val (_, rt) = runtime()
        rt.play(Layer.BASE, "wave", loop = false, fadeSeconds = 0f)
        rt.update(5f)   // clamped to 0.1 s
        assertEquals(9.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 1.0)
    }

    @Test fun stopFadesBackToRest() {
        val (_, rt) = runtime()
        rt.play(Layer.BASE, "wave", loop = false, fadeSeconds = 0f)
        repeat(30) { rt.update(1f / 30) }
        rt.stop(Layer.BASE, 0.3f)
        repeat(20) { rt.update(1f / 30) }
        assertEquals(0.0, PoseTestSupport.angleZDeg(rt.pose.rotation, 1), 1.0)
    }
}
