package ai.valis.character.pose

import ai.valis.character.CharacterState

/** What the character should be doing in a state, expressed as clip names. Absent clips are skipped, never fatal. */
class StatePlan(
    val base: String? = null,
    val baseLoop: Boolean = true,
    val gesture: String? = null,
    val face: String? = null,
    val faceLoop: Boolean = true,
    val faceGroups: Set<String> = EXPRESSION_GROUPS,
) {
    companion object {
        val EXPRESSION_GROUPS = setOf("BROW", "LID", "MOUTH", "VISEME")
        val SPEECH_GROUPS = setOf("MOUTH", "VISEME")
    }
}

object StatePlans {
    fun of(state: CharacterState): StatePlan = when (state) {
        CharacterState.DORMANT -> StatePlan()
        CharacterState.SUMMONED -> StatePlan(base = "idle", gesture = "wave_right", face = "expression_happy")
        CharacterState.IDLE -> StatePlan(base = "idle")
        CharacterState.LISTENING -> StatePlan(base = "idle", face = "expression_curious")
        CharacterState.THINKING -> StatePlan(base = "idle", gesture = "tilt_head", face = "expression_curious")
        CharacterState.SPEAKING -> StatePlan(base = "idle", face = "talk", faceGroups = StatePlan.SPEECH_GROUPS)
        CharacterState.ACTING -> StatePlan(base = "idle", gesture = "nod", face = "expression_excited")
        CharacterState.INTERRUPTED -> StatePlan(base = "idle", gesture = "startle", face = "expression_surprised")
        CharacterState.SLEEPING -> StatePlan(base = "droop", baseLoop = false, face = "expression_sleepy")
        CharacterState.ERROR -> StatePlan(base = "idle", gesture = "shrug", face = "expression_sad")
    }

    /** Applies [state] to [runtime], using the pack's meaningful masks for gestures so they never fight the base layer. */
    fun apply(runtime: PoseRuntime, pack: AnimationPack, state: CharacterState) {
        val plan = of(state)
        if (plan.base != null) runtime.play(Layer.BASE, plan.base, plan.baseLoop, 0.4f) else runtime.stop(Layer.BASE, 0.4f)
        if (plan.gesture != null) {
            val mask = pack.clip(plan.gesture)?.meaningfulMask
            runtime.play(Layer.GESTURE, plan.gesture, false, 0.2f, mask)
        } else runtime.stop(Layer.GESTURE, 0.3f)
        if (plan.face != null) runtime.play(Layer.FACE, plan.face, plan.faceLoop, 0.3f, groups = plan.faceGroups)
        else runtime.stop(Layer.FACE, 0.3f)
    }
}
