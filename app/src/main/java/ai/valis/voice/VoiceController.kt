package ai.valis.voice
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.*
import android.speech.tts.TextToSpeech
import java.util.Locale
/** On-demand recognition and speech output; not an always-on wake-word implementation. */
class VoiceController(private val context:Context,private val onPartial:(String)->Unit,private val onFinal:(String)->Unit,private val onError:(String)->Unit):TextToSpeech.OnInitListener{
 private var recognizer:SpeechRecognizer?=null;private var tts:TextToSpeech?=null;private var ready=false
 init{tts=TextToSpeech(context,this)}
 override fun onInit(status:Int){ready=status==TextToSpeech.SUCCESS;if(ready)tts?.language=Locale.getDefault()}
 fun startListening(){
  if(!SpeechRecognizer.isRecognitionAvailable(context)){onError("Speech recognition unavailable");return};stopListening()
  recognizer=SpeechRecognizer.createSpeechRecognizer(context).also{sr->
   sr.setRecognitionListener(object:RecognitionListener{
    override fun onReadyForSpeech(p:Bundle?){};override fun onBeginningOfSpeech(){};override fun onRmsChanged(r:Float){};override fun onBufferReceived(b:ByteArray?){};override fun onEndOfSpeech(){}
    override fun onError(e:Int){onError("Speech recognition error: $e")}
    override fun onResults(b:Bundle?){b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.let(onFinal)}
    override fun onPartialResults(b:Bundle?){b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()?.let(onPartial)}
    override fun onEvent(t:Int,b:Bundle?){}
   })
   sr.startListening(Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,true))
  }
 }
 fun speak(text:String){if(ready&&text.isNotBlank())tts?.speak(text,TextToSpeech.QUEUE_FLUSH,null,"valis-speech")}
 fun interrupt(){tts?.stop()}
 fun stopListening(){recognizer?.cancel();recognizer?.destroy();recognizer=null}
 fun release(){stopListening();tts?.shutdown();tts=null}
}
