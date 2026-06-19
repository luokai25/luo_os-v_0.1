package luoos.android.ai

import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import luoos.android.LuoOSApp
import luoos.android.MainActivity
import luoos.android.models.ModelDownloadManager

/**
 * LuoAiService — the heart of Luo OS.
 *
 * A persistent ForegroundService that:
 *  - Loads Gemma 4 E2B into memory on start
 *  - Keeps it loaded so responses are instant (no reload delay per message)
 *  - Exposes GemmaInference + LuoAgent via local Binder
 *  - Shows a minimal persistent notification (Android requirement for foreground services)
 *
 * Lifecycle:
 *  App launch → startForegroundService() → loadModel() → ready
 *  App killed → service continues via stopWithTask=false
 *  Device reboot → BootReceiver restarts the service
 */
class LuoAiService : Service() {

    companion object {
        private const val TAG = "LuoAiService"
        private const val NOTIF_ID = 1001

        const val ACTION_START = "luoos.ACTION_START"
        const val ACTION_STOP = "luoos.ACTION_STOP"
        const val ACTION_UNLOAD_MODEL = "luoos.ACTION_UNLOAD_MODEL"

        fun startIntent(context: Context) =
            Intent(context, LuoAiService::class.java).apply { action = ACTION_START }

        fun stopIntent(context: Context) =
            Intent(context, LuoAiService::class.java).apply { action = ACTION_STOP }
    }

    // ─── Service state ────────────────────────────────────────────────────────

    sealed class ServiceState {
        object Idle : ServiceState()
        object LoadingModel : ServiceState()
        object Ready : ServiceState()
        data class Error(val message: String) : ServiceState()
        object ModelNotDownloaded : ServiceState()
    }

    private val _state = MutableStateFlow<ServiceState>(ServiceState.Idle)
    val state: StateFlow<ServiceState> = _state

    // ─── Public AI components (bound clients use these) ───────────────────────

    lateinit var gemma: GemmaInference
        private set

    lateinit var agent: LuoAgent
        private set

    lateinit var tools: LuoTools
        private set

    // ─── Binder ───────────────────────────────────────────────────────────────

    inner class LuoBinder : Binder() {
        fun getService(): LuoAiService = this@LuoAiService
    }

    private val binder = LuoBinder()

    override fun onBind(intent: Intent): IBinder = binder

    // ─── Service lifecycle ────────────────────────────────────────────────────

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "LuoAiService created")

        val db = (application as LuoOSApp).database
        gemma = GemmaInference(this)
        tools = LuoTools(this, db.memoryDao())
        agent = LuoAgent(gemma, tools)

        startForeground(NOTIF_ID, buildNotification("Initializing..."))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START, null -> {
                if (_state.value !is ServiceState.Ready && _state.value !is ServiceState.LoadingModel) {
                    serviceScope.launch { initializeModel() }
                }
            }
            ACTION_STOP -> stopSelf()
            ACTION_UNLOAD_MODEL -> {
                gemma.unload()
                _state.value = ServiceState.Idle
                updateNotification("Model unloaded (save battery)")
            }
        }
        // START_STICKY: if killed, restart with null intent
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        gemma.unload()
        serviceScope.cancel()
        Log.i(TAG, "LuoAiService destroyed")
    }

    // ─── Model initialization ─────────────────────────────────────────────────

    private suspend fun initializeModel() {
        if (!gemma.isModelDownloaded) {
            Log.w(TAG, "Model not downloaded yet")
            _state.value = ServiceState.ModelNotDownloaded
            updateNotification("Model not downloaded — open Luo OS to download")
            return
        }

        _state.value = ServiceState.LoadingModel
        updateNotification("Loading Gemma 4 E2B...")

        val result = gemma.loadModel()

        if (result.isSuccess) {
            _state.value = ServiceState.Ready
            updateNotification("Ready")
            Log.i(TAG, "✓ Luo AI ready")
        } else {
            val error = result.exceptionOrNull()?.message ?: "Unknown error"
            _state.value = ServiceState.Error(error)
            updateNotification("Error loading model")
            Log.e(TAG, "Failed to load model: $error")
        }
    }

    // ─── Notification ─────────────────────────────────────────────────────────

    private fun buildNotification(status: String): Notification {
        val openAppIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return Notification.Builder(this, LuoOSApp.NOTIF_CHANNEL_AI)
            .setContentTitle("Luo OS")
            .setContentText(status)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentIntent(openAppIntent)
            .setOngoing(true)
            .setShowWhen(false)
            .build()
    }

    private fun updateNotification(status: String) {
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIF_ID, buildNotification(status))
    }
}
