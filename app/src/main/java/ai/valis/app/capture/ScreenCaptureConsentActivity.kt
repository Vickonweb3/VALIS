package ai.valis.app.capture
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.os.Bundle
/** Launches the system consent UI. Capture foreground service is a separate required integration. */
class ScreenCaptureConsentActivity:Activity(){
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);val m=getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager;startActivityForResult(m.createScreenCaptureIntent(),5102)}
 @Deprecated("Legacy callback retained for compatibility")
 override fun onActivityResult(requestCode:Int,resultCode:Int,data:Intent?){super.onActivityResult(requestCode,resultCode,data);if(requestCode==5102&&resultCode==RESULT_OK&&data!=null)setResult(RESULT_OK,Intent().putExtra("projection_result_code",resultCode).putExtra("projection_result_data",data))else setResult(RESULT_CANCELED);finish()}
}
