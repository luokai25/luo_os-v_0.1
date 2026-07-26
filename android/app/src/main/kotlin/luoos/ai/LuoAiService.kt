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

/**
 * LuoAiService — the heart of Luo OS.
 *
 * A persistent ForegroundService that:
 *  - Extracts the bundled Qwen2.5-1.5B GGUF model from APK assets on first launch
 *  - Loads it into memory on start (via llama.cpp, matching the laptop OS)
 *  - Keeps it loaded so responses are instant (no reload delay per message)
 *  - Exposes LlamaInference + LuoAgent via local Binder
 *  - Shows a minimal persistent notification (Android requirement for foreground services)
 *
 * Lifecycle:
 *  App launch → startForegroundService() → extract (first run only) → loadModel() → ready
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
        object Extracting : ServiceState()
        object LoadingModel : ServiceState()
        object Ready : ServiceState()
        data class Error(val message: String) : ServiceState()
    }

    private val _state = MutableStateFlow<ServiceState>(ServiceState.Idle)
    val state: StateFlow<ServiceState> = _state

    // ─── Public AI components (bound clients use these) ───────────────────────

    lateinit var llama: LlamaInference
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

    // SupervisorJob prevents sibling coroutine failures from cancelling each
    // other, but does NOT stop an uncaught exception from crashing the whole
    // app process — that requires an explicit handler. Without this, any
    // unexpected exception here (e.g. a file I/O race during model
    // extraction) takes down the entire app instead of just failing safely
    // into ServiceState.Error, which the UI already knows how to display.
    private val serviceExceptionHandler = CoroutineExceptionHandler { _, throwable ->
        Log.e(TAG, "Uncaught exception in LuoAiService coroutine scope", throwable)
        _state.value = ServiceState.Error(throwable.message ?: "Unexpected error")
        updateNotification("Error — see app for details")
    }

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main + serviceExceptionHandler)

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "LuoAiService created")

        val db = (application as LuoOSApp).database
        llama = LlamaInference(this)
        tools = LuoTools(this, db.memoryDao())
        agent = LuoAgent(llama, tools)

        startForeground(NOTIF_ID, buildNotification("Initializing..."))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START, null -> {
                // Only start initialization from Idle. This service can legitimately
                // receive startForegroundService() twice in quick succession —
                // MainActivity.onCreate() starts it, and ShellScreen's DisposableEffect
                // (fired on ON_START, ~1 frame later) calls bindService(), which also
                // calls startForegroundService(). Enumerating "not busy" states here
                // is fragile — a new busy state (like Extracting) can be added later
                // and silently bypass this guard, exactly as happened before this fix.
                // Guarding on "only Idle may start" is the only version of this check
                // that can't go stale when new states are added.
                if (_state.value is ServiceState.Idle) {
                    serviceScope.launch { initializeModel() }
                }
            }
            ACTION_STOP -> stopSelf()
            ACTION_UNLOAD_MODEL -> {
                llama.unload()
                _state.value = ServiceState.Idle
                updateNotification("Model unloaded (save battery)")
            }
        }
        // START_STICKY: if killed, restart with null intent
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        llama.unload()
        serviceScope.cancel()
        Log.i(TAG, "LuoAiService destroyed")
    }

    // ─── Model initialization ─────────────────────────────────────────────────

    private suspend fun initializeModel() {
        if (!llama.isModelReady) {
            _state.value = ServiceState.Extracting
            updateNotification("Setting up Luo AI (first launch only)...")

            val extractResult = llama.ensureModelExtracted()
            if (extractResult.isFailure) {
                val error = extractResult.exceptionOrNull()?.message ?: "Unknown error"
                _state.value = ServiceState.Error(error)
                updateNotification("Setup failed")
                Log.e(TAG, "Failed to extract bundled model: $error")
                return
            }
        }

        _state.value = ServiceState.LoadingModel
        updateNotification("Loading Qwen2.5-1.5B...")

        val result = llama.loadModel()

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
