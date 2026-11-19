package ai.valis.character

/** What VALIS is doing right now. Drives the character's behaviour; see pose/StatePlan. */
enum class CharacterState { DORMANT, SUMMONED, IDLE, LISTENING, THINKING, SPEAKING, ACTING, INTERRUPTED, SLEEPING, ERROR }

class CharacterStateMachine(private val onTransition: (CharacterState) -> Unit) {
    var state = CharacterState.DORMANT
        private set

    fun transition(next: CharacterState) {
        if (state != next) { state = next; onTransition(next) }
    }
}
