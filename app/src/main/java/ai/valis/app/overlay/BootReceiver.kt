package ai.valis.app.overlay

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Brings the overlay back after a restart, only if the user left it on and allows start-on-boot. */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED && intent.action != Intent.ACTION_MY_PACKAGE_REPLACED) return
        val prefs = OverlayPrefs(context)
        if (prefs.wanted && prefs.startOnBoot) OverlayController.start(context)
    }
}
