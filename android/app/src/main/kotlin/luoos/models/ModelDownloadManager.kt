package luoos.android.models

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import luoos.android.ai.GemmaInference
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL

/**
 * ModelDownloadManager — handles first-run model download.
 *
 * Downloads gemma-4-E2B-it-int4.bin from HuggingFace to internal storage.
 * Emits progress as a Flow<DownloadState> for the UI to display.
 *
 * NOTE: The model file (~1.3 GB) must be hosted on HuggingFace or your own CDN.
 * Update MODEL_URL before shipping.
 */
class ModelDownloadManager(private val context: Context) {

    companion object {
        private const val TAG = "ModelDownload"

        // Replace with your actual HuggingFace model URL after upload
        // Format: https://huggingface.co/<user>/<repo>/resolve/main/<filename>
        const val MODEL_URL = "https://huggingface.co/google/gemma-4-E2B-it-litert-lm/resolve/main/gemma-4-E2B-it-int4.bin"

        // Fallback: GGUF from unsloth (if LiteRT format is unavailable)
        const val MODEL_URL_FALLBACK = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-Q4_K_M.gguf"

        private const val BUFFER_SIZE = 8192
    }

    val modelDir: File get() = File(context.filesDir, "models").also { it.mkdirs() }
    val modelFile: File get() = File(modelDir, GemmaInference.MODEL_FILENAME)

    sealed class DownloadState {
        object Idle : DownloadState()
        data class Downloading(val bytesDownloaded: Long, val totalBytes: Long, val percent: Int) : DownloadState()
        object Processing : DownloadState()
        object Complete : DownloadState()
        data class Error(val message: String) : DownloadState()
    }

    fun downloadModel(): Flow<DownloadState> = flow {
        emit(DownloadState.Downloading(0L, 0L, 0))

        val tempFile = File(modelDir, "${GemmaInference.MODEL_FILENAME}.part")

        try {
            val url = URL(MODEL_URL)
            val connection = url.openConnection() as HttpURLConnection
            connection.apply {
                requestMethod = "GET"
                connectTimeout = 15_000
                readTimeout = 60_000
                setRequestProperty("User-Agent", "LuoOS/0.2 Android")
            }

            val responseCode = connection.responseCode
            if (responseCode != HttpURLConnection.HTTP_OK) {
                emit(DownloadState.Error("Server returned $responseCode"))
                return@flow
            }

            val totalBytes = connection.contentLengthLong
            Log.i(TAG, "Downloading model: ${formatBytes(totalBytes)}")

            var downloadedBytes = 0L
            val buffer = ByteArray(BUFFER_SIZE)

            connection.inputStream.use { input ->
                FileOutputStream(tempFile).use { output ->
                    var bytesRead: Int
                    var lastEmitPercent = -1

                    while (input.read(buffer).also { bytesRead = it } != -1) {
                        output.write(buffer, 0, bytesRead)
                        downloadedBytes += bytesRead

                        val percent = if (totalBytes > 0) {
                            ((downloadedBytes.toDouble() / totalBytes) * 100).toInt()
                        } else 0

                        // Emit every 1% to avoid flooding
                        if (percent != lastEmitPercent) {
                            lastEmitPercent = percent
                            emit(DownloadState.Downloading(downloadedBytes, totalBytes, percent))
                        }
                    }
                }
            }

            Log.i(TAG, "Download complete. Verifying...")
            emit(DownloadState.Processing)

            // Basic size sanity check (> 100 MB)
            if (tempFile.length() < 100_000_000L) {
                tempFile.delete()
                emit(DownloadState.Error("Downloaded file too small — may be corrupt"))
                return@flow
            }

            // Rename temp → final
            if (tempFile.renameTo(modelFile)) {
                Log.i(TAG, "Model saved to ${modelFile.absolutePath}")
                emit(DownloadState.Complete)
            } else {
                emit(DownloadState.Error("Failed to save model file"))
            }

        } catch (e: Exception) {
            Log.e(TAG, "Download failed", e)
            tempFile.delete()
            emit(DownloadState.Error("Download failed: ${e.message}"))
        }
    }.flowOn(Dispatchers.IO)

    fun deleteModel() {
        modelFile.delete()
        Log.i(TAG, "Model deleted")
    }

    private fun formatBytes(bytes: Long): String = when {
        bytes >= 1_073_741_824 -> "%.1f GB".format(bytes / 1_073_741_824.0)
        bytes >= 1_048_576 -> "%.1f MB".format(bytes / 1_048_576.0)
        else -> "$bytes B"
    }
}
