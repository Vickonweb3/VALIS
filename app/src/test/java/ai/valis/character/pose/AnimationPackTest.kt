package ai.valis.character.pose

import org.junit.Assert.*
import org.junit.Test

class AnimationPackTest {
    @Test fun parsesIndexAndDecodesRotation() {
        val b = PoseTestSupport.build()
        val pack = AnimationPack.parse(b.json, b.payload)
        assertEquals(listOf("root", "arm"), pack.joints)
        assertEquals(30, pack.fps)
        val clip = pack.clip("wave")!!
        val out = FloatArray(4)
        pack.rotation(clip.joints[0].rotation, clip.frames - 1, out, 0)
        assertEquals(90.0, Math.toDegrees(2 * Math.atan2(out[2].toDouble(), out[3].toDouble())), 0.1)
    }

    @Test fun rejectsWrongFormat() {
        val b = PoseTestSupport.build()
        assertThrows(PackFormatException::class.java) { AnimationPack.parse(b.json.replace("valis_anim.v1", "v0"), b.payload) }
    }

    @Test fun rejectsTruncatedPayload() {
        val b = PoseTestSupport.build()
        assertThrows(PackFormatException::class.java) { AnimationPack.parse(b.json, b.payload.copyOf(b.payload.size / 2)) }
    }

    @Test fun rejectsJointIndexOutOfRange() {
        val b = PoseTestSupport.build()
        assertThrows(PackFormatException::class.java) { AnimationPack.parse(b.json.replace("\"joint\":1", "\"joint\":9"), b.payload) }
    }

    @Test fun rejectsCountThatDisagreesWithFrames() {
        val b = PoseTestSupport.build()
        assertThrows(PackFormatException::class.java) { AnimationPack.parse(b.json.replace("\"count\":124", "\"count\":120"), b.payload) }
    }

    @Test fun rejectsGarbage() {
        assertThrows(PackFormatException::class.java) { AnimationPack.parse("not json", ByteArray(0)) }
    }
}
