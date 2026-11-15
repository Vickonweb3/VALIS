package ai.valis.app.actions
import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
class ValisAccessibilityService:AccessibilityService(){
 override fun onAccessibilityEvent(event:AccessibilityEvent?){}
 override fun onInterrupt(){}
 fun performApprovedAction(action:ApprovedDeviceAction):Boolean=when(action){
  ApprovedDeviceAction.BACK->performGlobalAction(GLOBAL_ACTION_BACK)
  ApprovedDeviceAction.HOME->performGlobalAction(GLOBAL_ACTION_HOME)
  ApprovedDeviceAction.NOTIFICATIONS->performGlobalAction(GLOBAL_ACTION_NOTIFICATIONS)
  ApprovedDeviceAction.QUICK_SETTINGS->performGlobalAction(GLOBAL_ACTION_QUICK_SETTINGS)
 }
}
enum class ApprovedDeviceAction{BACK,HOME,NOTIFICATIONS,QUICK_SETTINGS}
