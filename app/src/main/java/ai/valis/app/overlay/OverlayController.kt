package ai.valis.app.overlay

import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.core.content.ContextCompat

/** The only way the rest of the app starts or stops the overlay. */
object OverlayController {
    const val ACTION_STOP = "ai.valis.action.STOP_OVERLAY"

    /** Returns false if Android would not let the overlay start (missing permission, or background-start block). */
    fun start(c: Context): Boolean {
        if (!Settings.canDrawOverlays(c)) return false
        OverlayPrefs(c).wanted = true
        return try {
            ContextCompat.startForegroundService(c, Intent(c, CharacterOverlayService::class.java))
            true
        } catch (e: RuntimeException) {
            // e.g. ForegroundServiceStartNotAllowedException when called from the background.
            false
        }
    }

    fun stop(c: Context) {
        OverlayPrefs(c).wanted = false
        c.stopService(Intent(c, CharacterOverlayService::class.java))
    }
}
