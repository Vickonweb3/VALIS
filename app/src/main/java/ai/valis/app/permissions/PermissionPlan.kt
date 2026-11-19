package ai.valis.app.permissions

/** What VALIS can ask for, in the order it is asked. Pure Kotlin so it is unit-testable on the JVM. */
enum class Grant(val title: String, val why: String, val required: Boolean) {
    OVERLAY("Show over other apps", "Lets VALIS float above whatever you are doing.", true),
    NOTIFICATIONS("Notifications", "Shows the VALIS status chip with a Stop button.", true),
    BATTERY("Keep running in background", "Stops Android from putting VALIS to sleep.", false),
    ACCESSIBILITY("Control the screen for you", "Lets VALIS tap, scroll and navigate when you ask. You can turn it off anytime.", false),
}

data class GrantState(val granted: Set<Grant>) {
    fun has(g: Grant) = g in granted
}

object PermissionPlan {
    /** Order matters: the overlay first so the character can appear as early as possible. */
    val order: List<Grant> = listOf(Grant.OVERLAY, Grant.NOTIFICATIONS, Grant.BATTERY, Grant.ACCESSIBILITY)

    /** The next grant to ask for, or null when everything has been granted. */
    fun next(state: GrantState): Grant? = order.firstOrNull { !state.has(it) }

    /** VALIS may start once every required grant is present. */
    fun canStart(state: GrantState): Boolean = Grant.values().filter { it.required }.all { state.has(it) }

    fun missing(state: GrantState): List<Grant> = order.filter { !state.has(it) }

    /** Notifications only need a runtime grant from Android 13 (API 33). */
    fun notificationsNeedRuntimeGrant(sdk: Int): Boolean = sdk >= 33
}
