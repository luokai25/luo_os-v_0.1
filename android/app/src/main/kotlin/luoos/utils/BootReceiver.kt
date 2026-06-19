package luoos.android.utils

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import luoos.android.ai.LuoAiService

/**
 * BootReceiver — auto-starts LuoAiService after device reboot.
 * Registered in AndroidManifest.xml for BOOT_COMPLETED.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED ||
            intent.action == "android.intent.action.QUICKBOOT_POWERON") {
            Log.i("BootReceiver", "Device booted — starting Luo AI Service")
            context.startForegroundService(LuoAiService.startIntent(context))
        }
    }
}
