package ai.valis.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import androidx.appcompat.app.AppCompatActivity
import ai.valis.app.overlay.CharacterOverlayService

/**
 * Temporary developer entry point.
 * The polished companion/settings UI is intentionally deferred until the character works.
 */
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (Settings.canDrawOverlays(this)) {
            startOverlay()
            finish()
        } else {
            startActivity(
                Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")
                )
            )
        }
    }

    override fun onResume() {
        super.onResume()
        if (Settings.canDrawOverlays(this)) {
            startOverlay()
            finish()
        }
    }

    private fun startOverlay() {
        val intent = Intent(this, CharacterOverlayService::class.java)
        startForegroundService(intent)
    }
}
