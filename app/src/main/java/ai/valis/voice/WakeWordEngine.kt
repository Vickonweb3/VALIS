package ai.valis.voice
/** Plug in a licensed low-power on-device wake-word engine and "Yo VALIS" model. */
interface WakeWordEngine {
    fun start(onDetected:()->Unit,onFailure:(Throwable)->Unit)
    fun stop()
    val isRunning:Boolean
}
