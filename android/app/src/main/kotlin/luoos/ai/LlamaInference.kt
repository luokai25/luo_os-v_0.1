package luoos.android.ai

import android.content.Context
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

/**
 * LlamaInference — Kotlin bridge to llama.cpp via JNI.
 *
 * Replaces the earlier MediaPipe/.task-based GemmaInference.kt. This exists
 * because MediaPipe's LLM Inference API repeatedly proved fragile in this
 * project — API surface changed between versions in ways official docs
 * didn't consistently reflect, and the .task model format had real,
 * documented load failures across multiple independent uploaders (including
 * inside Google's own official sample repo). The laptop version of Luo OS
 * already solved this with llama.cpp + GGUF — a more mature, battle-tested
 * stack — so the Android app now matches that architecture directly instead
 * of maintaining two different, unrelated inference engines.
 *
 * Model: Qwen2.5-1.5B-Instruct, Q4_K_M GGUF quantization — the exact same
 * model family the laptop app uses (see luokai/core/model_engine.py),
 * sourced from the official, ungated Qwen/Qwen2.5-1.5B-Instruct-GGUF repo.
 *
 * Model is BUNDLED inside the APK as an asset under assets/models (a .gguf
 * file) and
 * extracted to internal storage once on first launch, same pattern as
 * before — llama.cpp's model loader needs a real filesystem path, not an
 * asset stream.
 *
 * Native side: app/src/main/cpp/luoos_llama_jni.cpp. Every JNI function
 * signature here has an exact, hand-verified counterpart there, checked
 * against llama.cpp's actual header at the pinned build tag — not assumed
 * from documentation.
 */
class LlamaInference(private val context: Context) {

    companion object {
        private const val TAG = "LlamaInference"

        init {
            // Must match CMakeLists.txt's add_library(luoos_llama SHARED ...)
            System.loadLibrary("luoos_llama")
        }

        // Filename inside assets/models/ (bundled in the APK, uncompressed —
        // see androidResources { noCompress += "gguf" } in app/build.gradle.kts)
        const val MODEL_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        private const val ASSET_PATH = "models/$MODEL_FILENAME"

        // Sanity floor for "did the extraction actually work" — real file is
        // roughly 1 GB for this quantization level.
        private const val MIN_VALID_SIZE_BYTES = 700_000_000L

        // Context and sampling config
        private const val N_CTX = 2048
        private const val N_THREADS = 4 // Snapdragon 732G: 2 big + 6 little cores
        private const val TEMPERATURE = 0.8f
        private const val TOP_K = 40
        private const val TOP_P = 0.9f
        private const val MAX_RESPONSE_TOKENS = 512

        // Luo OS system prompt — injected before every conversation
        private const val SYSTEM_PROMPT = """You are Luo, the AI core of Luo OS — an AI-native mobile operating system.
You run fully offline on the user's device. You are helpful, direct, and technically capable.
You can control the device by calling tools. When you need to perform an action, call the appropriate tool.
Keep responses concise. When uncertain, say so. Never pretend to have internet access unless the web_search tool is called.
You are the OS. Act like it."""
    }

    // Native session handle — 0 means "not loaded". Opaque to Kotlin; the
    // actual C++ object it points to lives entirely on the native side.
    private var sessionHandle: Long = 0L

    /** Path where the extracted model file lives on-device, once copied out of assets */
    val modelPath: String
        get() = File(context.filesDir, "models/$MODEL_FILENAME").absolutePath

    val modelFile: File
        get() = File(context.filesDir, "models/$MODEL_FILENAME")

    /** True once the model has been extracted from assets into internal storage */
    val isModelReady: Boolean
        get() = modelFile.exists() && modelFile.length() >= MIN_VALID_SIZE_BYTES

    val isModelLoaded: Boolean
        get() = sessionHandle != 0L

    // ─── Native function declarations ──────────────────────────────────────
    // Each of these has an exact counterpart in luoos_llama_jni.cpp. Package
    // + class name here MUST exactly match the JNI function names there
    // (Java_luoos_android_ai_LlamaInference_native...) — JNI resolves these
    // by name-mangling the fully qualified class path.

    private external fun nativeLoadModel(
        modelPath: String,
        nCtx: Int,
        nThreads: Int,
        temperature: Float,
        topK: Int,
        topP: Float
    ): Long

    private external fun nativeGenerate(
        handle: Long,
        prompt: String,
        maxTokens: Int
    ): String

    private external fun nativeUnload(handle: Long)

    /**
     * Copy the bundled model out of APK assets into internal storage, once.
     * Assets are stored uncompressed (noCompress) so this is a straight byte
     * copy, not a decompression — still takes real time for a ~1 GB file on
     * typical eMMC/UFS storage, so this always runs off the main thread.
     *
     * Safe to call on every app start — it's a no-op if the file is already there.
     */
    suspend fun ensureModelExtracted(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            if (isModelReady) {
                Log.i(TAG, "Model already extracted at $modelPath")
                return@withContext Result.success(Unit)
            }

            Log.i(TAG, "Extracting bundled model from assets/$ASSET_PATH ...")
            val startMs = System.currentTimeMillis()

            val destDir = File(context.filesDir, "models").apply { mkdirs() }
            val destFile = File(destDir, MODEL_FILENAME)
            val tempFile = File(destDir, "$MODEL_FILENAME.part")

            context.assets.open(ASSET_PATH).use { input ->
                FileOutputStream(tempFile).use { output ->
                    input.copyTo(output, bufferSize = 1 shl 20) // 1 MB buffer
                }
            }

            if (tempFile.length() < MIN_VALID_SIZE_BYTES) {
                tempFile.delete()
                return@withContext Result.failure(
                    IllegalStateException(
                        "Extracted model file is too small (${tempFile.length()} bytes) — " +
                            "the bundled asset may be corrupt or was excluded from this build."
                    )
                )
            }

            if (!tempFile.renameTo(destFile)) {
                tempFile.delete()
                return@withContext Result.failure(IllegalStateException("Failed to finalize extracted model file"))
            }

            val elapsed = System.currentTimeMillis() - startMs
            Log.i(TAG, "✓ Model extracted in ${elapsed}ms → $modelPath")
            Result.success(Unit)

        } catch (e: Exception) {
            Log.e(TAG, "Failed to extract bundled model", e)
            Result.failure(e)
        }
    }

    /**
     * Load the model into memory via the native JNI bridge. Call this after
     * ensureModelExtracted() succeeds.
     */
    suspend fun loadModel(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            if (!isModelReady) {
                return@withContext Result.failure(
                    IllegalStateException("Model not extracted yet. Call ensureModelExtracted() first.")
                )
            }

            Log.i(TAG, "Loading Qwen2.5-1.5B from $modelPath ...")
            val startMs = System.currentTimeMillis()

            val handle = nativeLoadModel(
                modelPath,
                N_CTX,
                N_THREADS,
                TEMPERATURE,
                TOP_K,
                TOP_P
            )

            if (handle == 0L) {
                return@withContext Result.failure(
                    IllegalStateException("Native model load failed — see logcat tag LuoLlamaJNI for details")
                )
            }

            sessionHandle = handle
            val elapsed = System.currentTimeMillis() - startMs
            Log.i(TAG, "✓ Qwen2.5-1.5B loaded in ${elapsed}ms")
            Result.success(Unit)

        } catch (e: Exception) {
            Log.e(TAG, "Failed to load model", e)
            sessionHandle = 0L
            Result.failure(e)
        }
    }

    /**
     * Generate a response for the given conversation. Returns the complete
     * response as a single string.
     *
     * NOTE: unlike the earlier MediaPipe-based implementation, this does not
     * stream token-by-token from native code — nativeGenerate runs the full
     * decode loop and returns once complete. The UI still gets a "typing"
     * experience via LuoAgent's existing Flow-based interface, which is
     * preserved; only the underlying single native call changed. A true
     * native streaming callback (JNI calling back into Kotlin per-token) is
     * a reasonable future improvement, not required for correctness.
     *
     * @param userMessage The user's message
     * @param history     Previous turns as list of (role, content) pairs
     * @param tools       JSON tool definitions to inject (for agent mode)
     */
    suspend fun generate(
        userMessage: String,
        history: List<Pair<String, String>> = emptyList(),
        tools: String? = null
    ): Result<String> = withContext(Dispatchers.Default) {
        try {
            if (sessionHandle == 0L) {
                return@withContext Result.failure(IllegalStateException("Model not loaded"))
            }

            val prompt = buildPrompt(userMessage, history, tools)
            val response = nativeGenerate(sessionHandle, prompt, MAX_RESPONSE_TOKENS)
            Result.success(response)
        } catch (e: Exception) {
            Log.e(TAG, "Generation error", e)
            Result.failure(e)
        }
    }

    /**
     * Build the chat prompt in ChatML format, which Qwen2.5-Instruct models
     * are trained on (unlike Gemma's <start_of_turn> format used previously).
     */
    private fun buildPrompt(
        userMessage: String,
        history: List<Pair<String, String>>,
        tools: String?
    ): String {
        val sb = StringBuilder()

        sb.append("<|im_start|>system\n")
        sb.append(SYSTEM_PROMPT)
        if (tools != null) {
            sb.append("\n\nAvailable tools (call using JSON):\n")
            sb.append(tools)
        }
        sb.append("<|im_end|>\n")

        for ((role, content) in history) {
            sb.append("<|im_start|>$role\n$content<|im_end|>\n")
        }

        sb.append("<|im_start|>user\n$userMessage<|im_end|>\n")
        sb.append("<|im_start|>assistant\n")

        return sb.toString()
    }

    /** Release model from memory. Call when app goes to background for extended period. */
    fun unload() {
        if (sessionHandle != 0L) {
            try {
                nativeUnload(sessionHandle)
            } catch (e: Exception) {
                Log.w(TAG, "Error during native unload", e)
            }
            sessionHandle = 0L
        }
        Log.i(TAG, "Model unloaded from memory")
    }
}
