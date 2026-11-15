package ai.valis.character

/**
 * Contract between VALIS behaviour and the concrete 3D renderer.
 * Keep model-specific bone/clip names in an asset profile, not scattered through behaviour code.
 */
interface CharacterRenderer {
    fun loadModel(assetPath: String, onLoaded: (CharacterModelInfo) -> Unit, onError: (Throwable) -> Unit)
    fun playAnimation(name: String, loop: Boolean = false, crossFadeSeconds: Float = 0.25f)
    fun stopAnimation()
    fun setPlaybackSpeed(speed: Float)
    fun setMorphTarget(name: String, weight: Float)
    fun setBoneRotation(boneName: String, x: Float, y: Float, z: Float)
}

data class CharacterModelInfo(
    val animationClips: List<String>,
    val boneNames: List<String>,
    val morphTargetNames: List<String>
)

enum class CharacterState {
    DORMANT, IDLE, LISTENING, THINKING, SPEAKING, ACTING, SLEEPING, INTERRUPTED
}

interface CharacterBehaviour {
    fun onStateChanged(state: CharacterState)
    fun onUserInteraction(event: CharacterEvent)
}

sealed interface CharacterEvent {
    data object Summoned : CharacterEvent
    data object Dismissed : CharacterEvent
    data object SpeechStarted : CharacterEvent
    data object SpeechEnded : CharacterEvent
    data class EmotionDetected(val emotion: String) : CharacterEvent
    data class ActionStarted(val action: String) : CharacterEvent
    data class ActionFinished(val action: String, val success: Boolean) : CharacterEvent
}
