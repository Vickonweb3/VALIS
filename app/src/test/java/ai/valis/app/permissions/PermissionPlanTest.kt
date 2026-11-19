package ai.valis.app.permissions

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PermissionPlanTest {
    @Test fun overlayIsAskedFirst() = assertEquals(Grant.OVERLAY, PermissionPlan.next(GrantState(emptySet())))

    @Test fun nextSkipsGrantedItems() =
        assertEquals(Grant.BATTERY, PermissionPlan.next(GrantState(setOf(Grant.OVERLAY, Grant.NOTIFICATIONS))))

    @Test fun nullWhenEverythingGranted() = assertNull(PermissionPlan.next(GrantState(Grant.values().toSet())))

    @Test fun cannotStartWithoutOverlay() = assertFalse(PermissionPlan.canStart(GrantState(setOf(Grant.NOTIFICATIONS))))

    @Test fun cannotStartWithoutNotifications() = assertFalse(PermissionPlan.canStart(GrantState(setOf(Grant.OVERLAY))))

    @Test fun optionalGrantsDoNotBlockStart() =
        assertTrue(PermissionPlan.canStart(GrantState(setOf(Grant.OVERLAY, Grant.NOTIFICATIONS))))

    @Test fun missingKeepsAskOrder() =
        assertEquals(listOf(Grant.BATTERY, Grant.ACCESSIBILITY), PermissionPlan.missing(GrantState(setOf(Grant.OVERLAY, Grant.NOTIFICATIONS))))

    @Test fun notificationRuntimeGrantStartsAtApi33() {
        assertFalse(PermissionPlan.notificationsNeedRuntimeGrant(32))
        assertTrue(PermissionPlan.notificationsNeedRuntimeGrant(33))
    }
}
