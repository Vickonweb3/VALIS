package ai.valis.character

interface CharacterRenderer {
    fun loadModel(assetPath:String,onLoaded:(CharacterModelInfo)->Unit,onError:(Throwable)->Unit)
    fun playAnimation(name:String,loop:Boolean=false,crossFadeSeconds:Float=0.25f)
    fun stopAnimation()
    fun setPlaybackSpeed(speed:Float)
    fun setMorphTarget(name:String,weight:Float)
    fun setBoneRotation(boneName:String,x:Float,y:Float,z:Float)
}
data class CharacterModelInfo(val animationClips:List<String>,val boneNames:List<String>,val morphTargetNames:List<String>)
enum class CharacterState { DORMANT,IDLE,LISTENING,THINKING,SPEAKING,ACTING,SLEEPING,INTERRUPTED }
class CharacterStateMachine(private val onTransition:(CharacterState)->Unit) {
    var state=CharacterState.DORMANT; private set
    fun transition(next:CharacterState){if(state!=next){state=next;onTransition(next)}}
}
