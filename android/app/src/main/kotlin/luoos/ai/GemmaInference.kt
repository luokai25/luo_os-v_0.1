package luoos.android.ai

import android.content.Context
import android.util.Log
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInference.LlmInferenceOptions
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession.LlmInferenceSessionOptions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

/**
 * GemmaInference — wraps MediaPipe LiteRT for Gemma 3 1B-IT
 *
 * Model is BUNDLED inside the APK as an asset (assets/models/gemma3-1b-it-int4.task,
 * ~555 MB) — no runtime download, no network dependency at first launch.
 *
 * On first launch, the model is copied once from compressed APK assets into
 * app-private internal storage, since MediaPipe's LlmInference.createFromOptions
 * requires a real filesystem path (setModelPath), not an AssetFileDescriptor.
 * Subsequent launches skip the copy if the file already exists.
 *
 * ARCHITECTURE NOTE (fixed after comparing against Google's own AI Edge Gallery
 * reference app, the raw MediaPipe source on GitHub, and a real, exactly-matched
 * bug report using this same model file): this uses the two-object engine +
 * session pattern that every real, confirmed-working implementation uses.
 * LlmInference.LlmInferenceOptions reliably supports setModelPath/setMaxTokens/
 * setPreferredBackend; sampling parameters (setTopK/setTemperature/
 * setRandomSeed) live on the separate LlmInferenceSession's options instead.
 *
 * The deeper root cause this session uncovered: the project's pinned
 * MediaPipe tasks-genai version (0.10.14, from May 2024) was roughly two
 * years stale relative to every confirmed-working reference — the AI Edge
 * Gallery app and the real bug report above both ran on 0.10.21+. Upgraded
 * the pinned version accordingly rather than just reworking the calling code
 * around an old API surface.
 *
 * Target hardware: Snapdragon 732G (Poco X3 NFC)
 * Model: Gemma 3 1B-IT INT4 (~555 MB on disk)
 * Expected speed: faster than a 2-4B class model on the same CPU — smaller model,
 * meaningfully quicker time-to-first-token and tokens/sec on a 2021 mid-range SoC.
 */
class GemmaInference(private val context: Context) {

    companion object {
        private const val TAG = "GemmaInference"

        // Filename inside assets/models/ (bundled in the APK, uncompressed — see
        // androidResources { noCompress += "task" } in app/build.gradle.kts)
        const val MODEL_FILENAME = "gemma3-1b-it-int4.task"
        private const val ASSET_PATH = "models/$MODEL_FILENAME"

        // Sanity floor for "did the extraction actually work" — real file is ~555 MB
        private const val MIN_VALID_SIZE_BYTES = 400_000_000L

        // Engine-level config (LlmInferenceOptions) — kept to the two fields that
        // are reliably present across MediaPipe tasks-genai versions.
        private const val MAX_TOKENS = 1024

        // Session-level sampling config (LlmInferenceSessionOptions) — this is
        // where TopK/Temperature/RandomSeed actually live per the real API.
        private const val TOP_K = 40
        private const val TEMPERATURE = 0.8f
        private const val RANDOM_SEED = 42

        // Luo OS system prompt — injected before every conversation
        private const val SYSTEM_PROMPT = """You are Luo, the AI core of Luo OS — an AI-native mobile operating system.
You run fully offline on the user's device. You are helpful, direct, and technically capable.
You can control the device by calling tools. When you need to perform an action, call the appropriate tool.
Keep responses concise. When uncertain, say so. Never pretend to have internet access unless the web_search tool is called.
You are the OS. Act like it."""
    }

    private var llmInference: LlmInference? = null
    private var session: LlmInferenceSession? = null
    private var isLoaded = false

    /** Path where the extracted model file lives on-device, once copied out of assets */
    val modelPath: String
        get() = File(context.filesDir, "models/$MODEL_FILENAME").absolutePath

    val modelFile: File
        get() = File(context.filesDir, "models/$MODEL_FILENAME")

    /** True once the model has been extracted from assets into internal storage */
    val isModelReady: Boolean
        get() = modelFile.exists() && modelFile.length() >= MIN_VALID_SIZE_BYTES

    val isModelLoaded: Boolean
        get() = isLoaded && llmInference != null && session != null

    /**
     * Copy the bundled model out of APK assets into internal storage, once.
     * Assets are stored uncompressed (noCompress) so this is a straight byte
     * copy, not a decompression — still takes a few seconds for 555 MB on
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
     * Load the model into memory and create an inference session. Call this
     * after ensureModelExtracted() succeeds. Takes roughly a few seconds on
     * Snapdragon 732G for a 1B-class model.
     */
    suspend fun loadModel(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            if (!isModelReady) {
                return@withContext Result.failure(
                    IllegalStateException("Model not extracted yet. Call ensureModelExtracted() first.")
                )
            }

            Log.i(TAG, "Loading Gemma 3 1B from $modelPath ...")
            val startMs = System.currentTimeMillis()

            // Engine-level options. setPreferredBackend is confirmed real —
            // verified directly against Google's own AI Edge Gallery
            // production source (LlmChatModelHelper.kt) and a matched real
            // bug report using this exact model file, both showing this
            // method on LlmInferenceOptions.builder(). CPU is the only
            // correct choice here: the Poco X3 NFC's Snapdragon 732G has no
            // usable GPU delegate path for this workload.
            val engineOptions = LlmInferenceOptions.builder()
                .setModelPath(modelPath)
                .setMaxTokens(MAX_TOKENS)
                .setPreferredBackend(LlmInference.Backend.CPU)
                .build()

            val inference = LlmInference.createFromOptions(context, engineOptions)

            // Session-level options: sampling parameters live here, per the
            // real, confirmed API (matches Google's own AI Edge Gallery app).
            val sessionOptions = LlmInferenceSessionOptions.builder()
                .setTopK(TOP_K)
                .setTemperature(TEMPERATURE)
                .setRandomSeed(RANDOM_SEED)
                .build()

            llmInference = inference
            session = LlmInferenceSession.createFromOptions(inference, sessionOptions)
            isLoaded = true

            val elapsed = System.currentTimeMillis() - startMs
            Log.i(TAG, "✓ Gemma 3 1B loaded in ${elapsed}ms")
            Result.success(Unit)

        } catch (e: Exception) {
            Log.e(TAG, "Failed to load model", e)
            isLoaded = false
            Result.failure(e)
        }
    }

    /**
     * Generate a streaming response token-by-token.
     * Returns a Flow<String> where each emission is a new token chunk.
     *
     * @param userMessage The user's message
     * @param history     Previous turns as list of (role, content) pairs
     * @param tools       JSON tool definitions to inject (for agent mode)
     */
    fun generateStreaming(
        userMessage: String,
        history: List<Pair<String, String>> = emptyList(),
        tools: String? = null
    ): Flow<String> = callbackFlow {

        val activeSession = session
            ?: throw IllegalStateException("Model not loaded")

        val prompt = buildPrompt(userMessage, history, tools)
        Log.d(TAG, "Prompt length: ${prompt.length} chars")

        try {
            // Real API: add the prompt to the session, then generate against
            // the session (not the engine) with a per-call progress listener.
            activeSession.addQueryChunk(prompt)
            activeSession.generateResponseAsync { partialResult, done ->
                trySend(partialResult)
                if (done) close()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Generation error", e)
            close(e)
        }

        awaitClose { }
    }

    /**
     * Non-streaming generation — returns full response string.
     * Use for tool result processing where you need the complete JSON.
     */
    suspend fun generate(
        userMessage: String,
        history: List<Pair<String, String>> = emptyList(),
        tools: String? = null
    ): Result<String> = withContext(Dispatchers.Default) {
        try {
            val activeSession = session
                ?: return@withContext Result.failure(IllegalStateException("Model not loaded"))

            val prompt = buildPrompt(userMessage, history, tools)
            activeSession.addQueryChunk(prompt)
            val response = activeSession.generateResponse()
            Result.success(response)
        } catch (e: Exception) {
            Log.e(TAG, "Generation error", e)
            Result.failure(e)
        }
    }

    /**
     * Build the Gemma chat prompt in the correct format.
     * Gemma uses <start_of_turn>user / <start_of_turn>model format.
     */
    private fun buildPrompt(
        userMessage: String,
        history: List<Pair<String, String>>,
        tools: String?
    ): String {
        val sb = StringBuilder()

        // System prompt as first user turn (Gemma doesn't have a system role)
        sb.append("<start_of_turn>user\n")
        sb.append(SYSTEM_PROMPT)

        if (tools != null) {
            sb.append("\n\nAvailable tools (call using JSON):\n")
            sb.append(tools)
        }

        sb.append("<end_of_turn>\n")
        sb.append("<start_of_turn>model\nUnderstood. I am Luo, your AI OS. Ready.<end_of_turn>\n")

        // Conversation history
        for ((role, content) in history) {
            val gemmaRole = if (role == "user") "user" else "model"
            sb.append("<start_of_turn>$gemmaRole\n$content<end_of_turn>\n")
        }

        // Current user message
        sb.append("<start_of_turn>user\n$userMessage<end_of_turn>\n")
        sb.append("<start_of_turn>model\n")

        return sb.toString()
    }

    /** Release model from memory. Call when app goes to background for extended period. */
    fun unload() {
        try {
            session?.close()
        } catch (e: Exception) {
            Log.w(TAG, "Error closing LlmInferenceSession", e)
        }
        try {
            llmInference?.close()
        } catch (e: Exception) {
            Log.w(TAG, "Error closing LlmInference", e)
        }
        session = null
        llmInference = null
        isLoaded = false
        Log.i(TAG, "Model unloaded from memory")
    }
}
