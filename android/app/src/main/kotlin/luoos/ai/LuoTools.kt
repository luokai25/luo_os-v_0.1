package luoos.android.ai

import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.MediaPlayer
import android.net.Uri
import android.os.Environment
import android.provider.AlarmClock
import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import luoos.android.LuoOSApp
import luoos.android.models.LuoMemoryDao
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

/**
 * LuoTools — all tools available to the Luo agent.
 *
 * Each tool:
 *  1. Has a name, description, and parameter schema
 *  2. Can be serialized to JSON for injection into the model prompt
 *  3. Has an execute() handler
 *
 * Gemma 4 E2B-it supports function calling natively.
 * The model outputs JSON like: {"tool": "list_files", "params": {"path": "/sdcard/DCIM"}}
 * LuoAgent parses this and calls the appropriate tool.
 */
class LuoTools(
    private val context: Context,
    private val memoryDao: LuoMemoryDao
) {
    companion object {
        private const val TAG = "LuoTools"
    }

    private val gson = Gson()

    // ─── Tool Registry ────────────────────────────────────────────────────────

    data class ToolDef(
        val name: String,
        val description: String,
        val params: Map<String, String>  // param name → description
    )

    val allTools = listOf(
        ToolDef(
            name = "list_files",
            description = "List files in a directory on the device",
            params = mapOf("path" to "Absolute path to directory, e.g. /sdcard/Download")
        ),
        ToolDef(
            name = "read_file_text",
            description = "Read the text content of a file (max 10KB)",
            params = mapOf("path" to "Absolute path to the file")
        ),
        ToolDef(
            name = "open_app",
            description = "Open an installed Android app by package name",
            params = mapOf("package_name" to "e.g. com.whatsapp, com.spotify.music")
        ),
        ToolDef(
            name = "set_alarm",
            description = "Set an alarm at a specific time",
            params = mapOf(
                "hour" to "Hour in 24h format (0–23)",
                "minute" to "Minute (0–59)",
                "label" to "Alarm label text"
            )
        ),
        ToolDef(
            name = "send_notification",
            description = "Show a system notification to the user",
            params = mapOf(
                "title" to "Notification title",
                "body" to "Notification body text"
            )
        ),
        ToolDef(
            name = "remember",
            description = "Save a piece of information to Luo's permanent memory",
            params = mapOf(
                "content" to "Text to remember",
                "tag" to "Optional tag/category for this memory"
            )
        ),
        ToolDef(
            name = "recall",
            description = "Search Luo's memory for stored information",
            params = mapOf("query" to "Search query to find relevant memories")
        ),
        ToolDef(
            name = "get_time",
            description = "Get the current date and time",
            params = emptyMap()
        ),
        ToolDef(
            name = "web_search",
            description = "Search the web (requires internet connection)",
            params = mapOf("query" to "Search query string")
        ),
        ToolDef(
            name = "open_url",
            description = "Open a URL in the default browser",
            params = mapOf("url" to "Full URL including https://")
        ),
        ToolDef(
            name = "list_installed_apps",
            description = "List all installed apps on the device",
            params = emptyMap()
        ),
        ToolDef(
            name = "get_storage_info",
            description = "Get device storage usage information",
            params = emptyMap()
        )
    )

    /** Serialize all tools to a JSON string for prompt injection */
    fun toPromptJson(): String {
        val list = allTools.map { tool ->
            buildString {
                append("{\n")
                append("  \"name\": \"${tool.name}\",\n")
                append("  \"description\": \"${tool.description}\",\n")
                append("  \"params\": {")
                append(tool.params.entries.joinToString(", ") { (k, v) -> "\"$k\": \"$v\"" })
                append("}\n}")
            }
        }
        return "[\n${list.joinToString(",\n")}\n]"
    }

    // ─── Tool Executor ────────────────────────────────────────────────────────

    /**
     * Execute a tool call parsed from model output.
     * Returns a result string to feed back to the model.
     */
    suspend fun execute(toolName: String, params: JsonObject): String =
        withContext(Dispatchers.IO) {
            Log.d(TAG, "Executing tool: $toolName with params: $params")
            try {
                when (toolName) {
                    "list_files" -> listFiles(params.get("path")?.asString ?: "/sdcard")
                    "read_file_text" -> readFileText(params.get("path")?.asString ?: "")
                    "open_app" -> openApp(params.get("package_name")?.asString ?: "")
                    "set_alarm" -> setAlarm(
                        params.get("hour")?.asInt ?: 8,
                        params.get("minute")?.asInt ?: 0,
                        params.get("label")?.asString ?: "Luo Alarm"
                    )
                    "send_notification" -> sendNotification(
                        params.get("title")?.asString ?: "Luo OS",
                        params.get("body")?.asString ?: ""
                    )
                    "remember" -> remember(
                        params.get("content")?.asString ?: "",
                        params.get("tag")?.asString
                    )
                    "recall" -> recall(params.get("query")?.asString ?: "")
                    "get_time" -> getTime()
                    "web_search" -> webSearch(params.get("query")?.asString ?: "")
                    "open_url" -> openUrl(params.get("url")?.asString ?: "")
                    "list_installed_apps" -> listInstalledApps()
                    "get_storage_info" -> getStorageInfo()
                    else -> "ERROR: Unknown tool '$toolName'"
                }
            } catch (e: Exception) {
                Log.e(TAG, "Tool execution error: $toolName", e)
                "ERROR: ${e.message}"
            }
        }

    // ─── Tool Implementations ─────────────────────────────────────────────────

    private fun listFiles(path: String): String {
        val dir = File(path)
        if (!dir.exists()) return "Directory not found: $path"
        if (!dir.isDirectory) return "Not a directory: $path"
        val files = dir.listFiles() ?: return "Cannot read directory (permission denied?)"
        if (files.isEmpty()) return "Directory is empty"
        val listing = files.sortedWith(compareBy({ !it.isDirectory }, { it.name }))
            .take(50)
            .joinToString("\n") { f ->
                val type = if (f.isDirectory) "DIR " else "FILE"
                val size = if (f.isFile) " (${formatBytes(f.length())})" else ""
                "[$type] ${f.name}$size"
            }
        return "Contents of $path (${files.size} items):\n$listing"
    }

    private fun readFileText(path: String): String {
        val file = File(path)
        if (!file.exists()) return "File not found: $path"
        if (!file.isFile) return "Not a file: $path"
        if (file.length() > 10_240) return "File too large (${formatBytes(file.length())}). Max 10 KB."
        return try {
            file.readText()
        } catch (e: Exception) {
            "Cannot read file: ${e.message}"
        }
    }

    private fun openApp(packageName: String): String {
        val pm = context.packageManager
        val intent = pm.getLaunchIntentForPackage(packageName)
            ?: return "App not found or not launchable: $packageName"
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        return "Opened $packageName"
    }

    private fun setAlarm(hour: Int, minute: Int, label: String): String {
        val intent = Intent(AlarmClock.ACTION_SET_ALARM).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            putExtra(AlarmClock.EXTRA_HOUR, hour)
            putExtra(AlarmClock.EXTRA_MINUTES, minute)
            putExtra(AlarmClock.EXTRA_MESSAGE, label)
            putExtra(AlarmClock.EXTRA_SKIP_UI, true)
        }
        context.startActivity(intent)
        return "Alarm set for ${hour.toString().padStart(2,'0')}:${minute.toString().padStart(2,'0')} — \"$label\""
    }

    private fun sendNotification(title: String, body: String): String {
        val manager = context.getSystemService(NotificationManager::class.java)
        val notification = android.app.Notification.Builder(context, LuoOSApp.NOTIF_CHANNEL_AGENT)
            .setContentTitle(title)
            .setContentText(body)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setAutoCancel(true)
            .build()
        manager.notify(System.currentTimeMillis().toInt(), notification)
        return "Notification sent: \"$title\""
    }

    private suspend fun remember(content: String, tag: String?): String {
        val memory = luoos.android.models.LuoMemory(
            content = content,
            tag = tag ?: "general",
            timestamp = System.currentTimeMillis()
        )
        memoryDao.insert(memory)
        return "Remembered: \"$content\"${if (tag != null) " [tag: $tag]" else ""}"
    }

    private suspend fun recall(query: String): String {
        val results = memoryDao.search("%$query%")
        if (results.isEmpty()) return "No memories found matching: \"$query\""
        return "Found ${results.size} memories:\n" + results.joinToString("\n") { mem ->
            val date = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault())
                .format(Date(mem.timestamp))
            "[${mem.tag}] $date: ${mem.content}"
        }
    }

    private fun getTime(): String {
        val sdf = SimpleDateFormat("EEEE, MMMM d yyyy — HH:mm:ss", Locale.getDefault())
        return sdf.format(Date())
    }

    private fun webSearch(query: String): String {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://search.brave.com/search?q=${Uri.encode(query)}"))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return try {
            context.startActivity(intent)
            "Opened web search for: \"$query\""
        } catch (e: Exception) {
            "Could not open browser: ${e.message}"
        }
    }

    private fun openUrl(url: String): String {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        return try {
            context.startActivity(intent)
            "Opened: $url"
        } catch (e: Exception) {
            "Could not open URL: ${e.message}"
        }
    }

    private fun listInstalledApps(): String {
        val pm = context.packageManager
        val apps = pm.getInstalledApplications(0)
            .filter { pm.getLaunchIntentForPackage(it.packageName) != null }
            .sortedBy { it.packageName }
            .take(30)
            .joinToString("\n") { app ->
                val label = app.loadLabel(pm).toString()
                "• $label (${app.packageName})"
            }
        return "Installed apps (launchable, max 30):\n$apps"
    }

    private fun getStorageInfo(): String {
        val internal = Environment.getDataDirectory().let {
            val total = it.totalSpace
            val free = it.freeSpace
            "Internal: ${formatBytes(total - free)} used / ${formatBytes(total)} total"
        }
        val external = Environment.getExternalStorageDirectory()?.let {
            if (it.exists()) {
                "External: ${formatBytes(it.totalSpace - it.freeSpace)} used / ${formatBytes(it.totalSpace)} total"
            } else null
        }
        return listOfNotNull(internal, external).joinToString("\n")
    }

    // ─── Utilities ────────────────────────────────────────────────────────────

    private fun formatBytes(bytes: Long): String = when {
        bytes >= 1_073_741_824 -> "%.1f GB".format(bytes / 1_073_741_824.0)
        bytes >= 1_048_576 -> "%.1f MB".format(bytes / 1_048_576.0)
        bytes >= 1_024 -> "%.1f KB".format(bytes / 1_024.0)
        else -> "$bytes B"
    }
}
