package ai.valis.app.overlay

import android.content.Context

/**
 * The user's intent, kept in plain storage so the service, boot receiver and UI agree.
 * `wanted` is true when the user started VALIS and has not stopped it. Stop always wins:
 * once the user taps Stop, nothing restarts the overlay until they start it again.
 */
class OverlayPrefs(context: Context) {
    private val p = context.applicationContext.getSharedPreferences("valis_overlay", Context.MODE_PRIVATE)

    var wanted: Boolean
        get() = p.getBoolean(KEY_WANTED, false)
        set(v) { p.edit().putBoolean(KEY_WANTED, v).apply() }

    /** Opt-in: start the overlay again after the phone restarts. */
    var startOnBoot: Boolean
        get() = p.getBoolean(KEY_BOOT, true)
        set(v) { p.edit().putBoolean(KEY_BOOT, v).apply() }

    private companion object { const val KEY_WANTED = "wanted"; const val KEY_BOOT = "start_on_boot" }
}
