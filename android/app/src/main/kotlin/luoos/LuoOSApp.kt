package luoos.android

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.util.Log
import luoos.android.ai.LuoAiService
import luoos.android.models.LuoDatabase

class LuoOSApp : Application() {

    companion object {
        const val TAG = "LuoOS"
        const val NOTIF_CHANNEL_AI = "luo_ai_service"
        const val NOTIF_CHANNEL_AGENT = "luo_agent_tasks"
        lateinit var instance: LuoOSApp
            private set
    }

    // Lazy DB instance shared across the app
    val database: LuoDatabase by lazy {
        LuoDatabase.getInstance(this)
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        Log.i(TAG, "⚡ Luo OS booting...")
        createNotificationChannels()
        Log.i(TAG, "✓ Luo OS ready")
    }

    private fun createNotificationChannels() {
        val manager = getSystemService(NotificationManager::class.java)

        // AI service persistent notification channel
        val aiChannel = NotificationChannel(
            NOTIF_CHANNEL_AI,
            "Luo AI Service",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Keeps Qwen2.5-1.5B loaded and ready"
            setShowBadge(false)
            enableVibration(false)
        }

        // Agent task notifications
        val agentChannel = NotificationChannel(
            NOTIF_CHANNEL_AGENT,
            "Luo Agent Tasks",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Notifications from autonomous agent tasks"
        }

        manager.createNotificationChannels(listOf(aiChannel, agentChannel))
        Log.d(TAG, "Notification channels created")
    }
}
