package ai.valis.app.overlay

import android.app.*
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.view.*
import android.widget.*
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import ai.valis.app.MainActivity

class CharacterOverlayService : Service() {
    private lateinit var wm: WindowManager
    private var root: LinearLayout? = null
    private var panel: LinearLayout? = null
    private lateinit var lp: WindowManager.LayoutParams
    private var expanded = false

    override fun onCreate() {
        super.onCreate()
        if (Build.VERSION.SDK_INT >= 26) {
            getSystemService(NotificationManager::class.java).createNotificationChannel(
                NotificationChannel(CHANNEL, "VALIS companion", NotificationManager.IMPORTANCE_LOW))
        }
        val type = if (Build.VERSION.SDK_INT >= 34) ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE else 0
        ServiceCompat.startForeground(this, ID, buildNotification(), type)
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
    }

    /** Always shows a Stop action: the user can end VALIS at any time. */
    private fun buildNotification(): Notification {
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE)
        val stop = PendingIntent.getService(this, 1,
            Intent(this, CharacterOverlayService::class.java).setAction(OverlayController.ACTION_STOP), PendingIntent.FLAG_IMMUTABLE)
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("VALIS is active")
            .setContentText("Tap to open. Stop turns VALIS off.").setOngoing(true)
            .setContentIntent(open).addAction(0, "Stop", stop).build()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == OverlayController.ACTION_STOP) {
            OverlayController.stop(this)
            return START_NOT_STICKY
        }
        // Without the overlay permission there is nothing to show; do not loop.
        if (!Settings.canDrawOverlays(this)) { stopSelf(); return START_NOT_STICKY }
        // A null intent means Android restarted us after killing the process: honour the user's last choice.
        if (intent == null && !OverlayPrefs(this).wanted) { stopSelf(); return START_NOT_STICKY }
        if (root == null) attach()
        return START_STICKY
    }

    private fun attach() {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(dp(8),dp(8),dp(8),dp(8))
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(0xEE0E0E19.toInt()); cornerRadius=dp(22).toFloat(); setStroke(dp(1),0xFF1B55FF.toInt())
            }
        }
        val head = LinearLayout(this).apply { gravity=Gravity.CENTER_VERTICAL }
        val avatar = TextView(this).apply {
            text="V"; textSize=22f; gravity=Gravity.CENTER; setTextColor(-1)
            background=android.graphics.drawable.GradientDrawable().apply { shape=android.graphics.drawable.GradientDrawable.OVAL; setColor(0xFF1B55FF.toInt()) }
            layoutParams=LinearLayout.LayoutParams(dp(48),dp(48))
        }
        head.addView(avatar)
        head.addView(TextView(this).apply { text="  VALIS"; textSize=15f; setTextColor(-1) }, LinearLayout.LayoutParams(0,dp(48),1f))
        head.addView(TextView(this).apply { text="•••"; textSize=18f; setTextColor(-1); setPadding(dp(8),0,dp(8),0); setOnClickListener { toggle() } })
        box.addView(head)
        panel=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL; visibility=View.GONE; setPadding(dp(4),dp(8),dp(4),0)
            addView(TextView(this@CharacterOverlayService).apply { text="Character renderer attachment point"; setTextColor(0xFFE3E4F1.toInt()) })
            addView(Button(this@CharacterOverlayService).apply { text="Turn off VALIS"; setOnClickListener { OverlayController.stop(this@CharacterOverlayService) } })
        }
        box.addView(panel)
        head.setOnTouchListener(DragTouch())
        lp=WindowManager.LayoutParams(WindowManager.LayoutParams.WRAP_CONTENT,WindowManager.LayoutParams.WRAP_CONTENT,
            if(Build.VERSION.SDK_INT>=26) WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY else WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,PixelFormat.TRANSLUCENT
        ).apply { gravity=Gravity.TOP or Gravity.END; x=dp(12); y=dp(130) }
        root=box; wm.addView(box,lp)
    }
    private fun toggle(){ expanded=!expanded; panel?.visibility=if(expanded) View.VISIBLE else View.GONE }
    private inner class DragTouch:View.OnTouchListener {
        var x=0; var y=0; var sx=0f; var sy=0f
        override fun onTouch(v:View,e:MotionEvent):Boolean {
            when(e.action){
                MotionEvent.ACTION_DOWN->{x=lp.x;y=lp.y;sx=e.rawX;sy=e.rawY;return true}
                MotionEvent.ACTION_MOVE->{lp.x=(x+sx-e.rawX).toInt();lp.y=(y+e.rawY-sy).toInt();wm.updateViewLayout(root,lp);return true}
            }; return e.action==MotionEvent.ACTION_UP
        }
    }
    private fun dp(v:Int)=(v*resources.displayMetrics.density).toInt()
    override fun onDestroy(){ root?.let{if(it.isAttachedToWindow)wm.removeView(it)};root=null;super.onDestroy() }
    override fun onBind(intent:Intent?):IBinder?=null
    companion object { private const val CHANNEL="valis_companion";private const val ID=4101 }
}
