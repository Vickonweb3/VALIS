package ai.valis.app

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import ai.valis.app.overlay.OverlayController
import ai.valis.app.overlay.OverlayPrefs
import ai.valis.app.permissions.Grant
import ai.valis.app.permissions.PermissionGate
import ai.valis.app.permissions.PermissionPlan

/**
 * Guided setup. Each grant is explained, then the user is sent to the real Android screen.
 * Android does not allow an app to grant itself access, so the user always makes the final choice.
 * The polished companion UI comes later; this screen is deliberately plain.
 */
class MainActivity : AppCompatActivity() {
    private lateinit var list: LinearLayout
    private lateinit var start: Button
    private lateinit var stop: Button
    private lateinit var prefs: OverlayPrefs

    private val askNotifications = registerForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        // If the system will not ask again, send the user to the settings screen instead.
        if (!ok) launch(PermissionGate.settingsIntent(this, Grant.NOTIFICATIONS))
        render()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // CI smoke test hook: honoured only in debuggable builds, never in a release APK.
        val debuggable = applicationInfo.flags and android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE != 0
        if (debuggable && intent.getBooleanExtra("valis_autostart", false)) ai.valis.app.overlay.OverlayController.start(this)
        prefs = OverlayPrefs(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setBackgroundColor(INK); setPadding(dp(20), dp(28), dp(20), dp(20))
        }
        root.addView(text("VALIS", 30f, Color.WHITE, bold = true))
        root.addView(text("Give VALIS the access it needs. You stay in control and can turn any of it off.", 15f, PEARL).apply { setPadding(0, dp(6), 0, dp(18)) })
        list = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(ScrollView(this).apply { addView(list) }, LinearLayout.LayoutParams(-1, 0, 1f))

        val boot = Switch(this).apply {
            text = "Start VALIS again after the phone restarts"; setTextColor(Color.WHITE); isChecked = prefs.startOnBoot
            setOnCheckedChangeListener { _, on -> prefs.startOnBoot = on }
            setPadding(0, dp(12), 0, dp(12))
        }
        root.addView(boot)
        start = button("Start VALIS", filled = true) {
            if (!OverlayController.start(this)) Toast.makeText(this, "Could not start. Check the permissions above.", Toast.LENGTH_LONG).show()
            else finish()
        }
        stop = button("Turn off VALIS", filled = false) { OverlayController.stop(this); render() }
        root.addView(start, rowParams()); root.addView(stop, rowParams())
        setContentView(root)
    }

    override fun onResume() { super.onResume(); render() }

    private fun render() {
        val state = PermissionGate.snapshot(this)
        list.removeAllViews()
        for (g in PermissionPlan.order) {
            val done = state.has(g)
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(14), dp(16), dp(14))
                background = GradientDrawable().apply { setColor(CARD); cornerRadius = dp(18).toFloat() }
            }
            card.addView(text(g.title + if (g.required) "" else "  (optional)", 16f, Color.WHITE, bold = true))
            card.addView(text(g.why, 14f, PEARL).apply { setPadding(0, dp(4), 0, dp(10)) })
            card.addView(if (done) text("Granted", 14f, 0xFF3DDC97.toInt(), bold = true)
                         else button("Grant", filled = true) { grant(g) })
            list.addView(card, rowParams())
        }
        val can = PermissionPlan.canStart(state)
        start.isEnabled = can; start.alpha = if (can) 1f else 0.4f
        stop.visibility = if (prefs.wanted) View.VISIBLE else View.GONE
    }

    private fun grant(g: Grant) {
        if (g == Grant.NOTIFICATIONS && PermissionPlan.notificationsNeedRuntimeGrant(Build.VERSION.SDK_INT)) {
            askNotifications.launch(Manifest.permission.POST_NOTIFICATIONS); return
        }
        if (g == Grant.BATTERY) {
            try { startActivity(PermissionGate.settingsIntent(this, g)) }
            catch (e: ActivityNotFoundException) { launch(PermissionGate.batteryFallbackIntent()) }
            return
        }
        launch(PermissionGate.settingsIntent(this, g))
    }

    private fun launch(i: Intent) {
        try { startActivity(i) } catch (e: ActivityNotFoundException) {
            Toast.makeText(this, "This phone has no screen for that setting.", Toast.LENGTH_LONG).show()
        }
    }

    private fun text(t: String, size: Float, color: Int, bold: Boolean = false) = TextView(this).apply {
        text = t; textSize = size; setTextColor(color); if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
    }

    private fun button(label: String, filled: Boolean, onClick: () -> Unit) = Button(this).apply {
        text = label; isAllCaps = false; minHeight = dp(48); gravity = Gravity.CENTER
        setTextColor(Color.WHITE)
        background = GradientDrawable().apply {
            cornerRadius = dp(14).toFloat()
            if (filled) setColor(COBALT) else { setColor(Color.TRANSPARENT); setStroke(dp(2), PEARL) }
        }
        setOnClickListener { onClick() }
    }

    private fun rowParams() = LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(12) }
    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    private companion object {
        const val INK = 0xFF0E0E19.toInt(); const val CARD = 0xFF1B1D33.toInt()
        const val COBALT = 0xFF1B55FF.toInt(); const val PEARL = 0xFFE3E4F1.toInt()
    }
}
