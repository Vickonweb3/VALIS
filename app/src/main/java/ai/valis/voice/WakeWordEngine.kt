package ai.valis.voice
/** Contract only: connect a licensed low-power on-device engine and the "Yo VALIS" model. */
interface WakeWordEngine{fun start(onDetected:()->Unit,onFailure:(Throwable)->Unit);fun stop();val isRunning:Boolean}
