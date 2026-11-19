package ai.valis.character.pose

import org.junit.Assert.*
import org.junit.Test

class RigBinderTest {
    private val pack = PoseTestSupport.build().let { AnimationPack.parse(it.json, it.payload) }
    private val nodes = mapOf("root" to 10, "arm" to 11, "face" to 12)

    @Test fun bindsByNameAndChecksMorphOrder() {
        val rig = RigBinder.bind(pack, { nodes[it] }, { listOf("blink", "smile") })
        assertArrayEquals(intArrayOf(10, 11), rig.jointEntities)
        assertEquals(12, rig.meshEntities["face"])
        assertEquals(2, rig.morphCounts["face"])
    }

    @Test fun reportsEveryProblemAtOnce() {
        val e = assertThrows(RigMismatchException::class.java) { RigBinder.bind(pack, { null }, { emptyList() }) }
        assertEquals(3, e.problems.size)
    }

    @Test fun rejectsMissingMorphTarget() {
        val e = assertThrows(RigMismatchException::class.java) { RigBinder.bind(pack, { nodes[it] }, { listOf("blink", "wink") }) }
        assertTrue(e.problems.single().contains("smile"))
    }

    @Test fun rejectsReorderedMorphTargets() {
        val e = assertThrows(RigMismatchException::class.java) { RigBinder.bind(pack, { nodes[it] }, { listOf("smile", "blink") }) }
        assertTrue(e.problems.single().contains("different order"))
    }

    @Test fun rejectsWrongMorphCount() {
        assertThrows(RigMismatchException::class.java) { RigBinder.bind(pack, { nodes[it] }, { listOf("blink") }) }
    }
}
