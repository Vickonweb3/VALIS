package ai.valis.character.pose

/** The rig in the loaded model does not match the animation pack. Lists every problem, not just the first. */
class RigMismatchException(val problems: List<String>) :
    IllegalStateException("Rig does not match animation pack:\n" + problems.joinToString("\n") { " - $it" })

/** Resolved handles for the loaded model: one engine entity per pack joint, and morph target counts per mesh. */
class Rig(val jointEntities: IntArray, val meshEntities: Map<String, Int>, val morphCounts: Map<String, Int>)

object RigBinder {
    /**
     * Binds the pack to a loaded model by name. A mismatch fails loudly at load time:
     * a half-bound character silently animating the wrong bones is worse than no character.
     *
     * @param resolveNode name -> engine entity, or null when the model has no such node
     * @param morphNames  entity -> morph target names, in model order (empty when none)
     */
    fun bind(pack: AnimationPack, resolveNode: (String) -> Int?, morphNames: (Int) -> List<String>): Rig {
        val problems = ArrayList<String>()
        val joints = IntArray(pack.joints.size)
        pack.joints.forEachIndexed { i, name ->
            val e = resolveNode(name)
            if (e == null) problems += "joint '$name' not found in model" else joints[i] = e
        }
        val meshes = LinkedHashMap<String, Int>()
        val counts = LinkedHashMap<String, Int>()
        for ((mesh, expected) in pack.morphs) {
            val e = resolveNode(mesh)
            if (e == null) { problems += "mesh '$mesh' not found in model"; continue }
            val actual = morphNames(e)
            if (actual != expected) {
                val missing = expected.filter { it !in actual }
                problems += when {
                    actual.size != expected.size -> "mesh '$mesh' has ${actual.size} morph targets, pack expects ${expected.size}"
                    missing.isNotEmpty() -> "mesh '$mesh' lacks morph targets: ${missing.joinToString()}"
                    else -> "mesh '$mesh' morph targets are in a different order than the pack"
                }
                continue
            }
            meshes[mesh] = e
            counts[mesh] = expected.size
        }
        if (problems.isNotEmpty()) throw RigMismatchException(problems)
        return Rig(joints, meshes, counts)
    }
}
