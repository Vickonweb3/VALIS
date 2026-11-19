package ai.valis.app.permissions

import android.Manifest
import android.app.NotificationManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.core.content.ContextCompat
import ai.valis.app.actions.ValisAccessibilityService

/** Reads real Android permission state and builds the intent that lets the user grant each one. */
object PermissionGate {

    fun snapshot(c: Context): GrantState {
        val g = mutableSetOf<Grant>()
        if (Settings.canDrawOverlays(c)) g += Grant.OVERLAY
        if (notificationsAllowed(c)) g += Grant.NOTIFICATIONS
        if (batteryExempt(c)) g += Grant.BATTERY
        if (accessibilityOn(c)) g += Grant.ACCESSIBILITY
        return GrantState(g)
    }

    private fun notificationsAllowed(c: Context): Boolean {
        if (PermissionPlan.notificationsNeedRuntimeGrant(Build.VERSION.SDK_INT) &&
            ContextCompat.checkSelfPermission(c, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) return false
        return c.getSystemService(NotificationManager::class.java).areNotificationsEnabled()
    }

    private fun batteryExempt(c: Context): Boolean =
        c.getSystemService(PowerManager::class.java).isIgnoringBatteryOptimizations(c.packageName)

    private fun accessibilityOn(c: Context): Boolean {
        val me = ComponentName(c, ValisAccessibilityService::class.java).flattenToString()
        val enabled = Settings.Secure.getString(c.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES) ?: return false
        return enabled.split(':').any { it.equals(me, ignoreCase = true) }
    }

    /** The system screen where the user grants [g]. Notifications on API 33+ use a runtime prompt instead (see MainActivity). */
    fun settingsIntent(c: Context, g: Grant): Intent = when (g) {
        Grant.OVERLAY -> Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:${c.packageName}"))
        Grant.NOTIFICATIONS -> Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE, c.packageName)
        Grant.BATTERY -> Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:${c.packageName}"))
        Grant.ACCESSIBILITY -> Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
    }

    /** Some OEMs lack the direct battery dialog; fall back to the general list. */
    fun batteryFallbackIntent(): Intent = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
}
