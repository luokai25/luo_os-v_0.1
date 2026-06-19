package luoos.android.ai

import android.content.Context
import android.util.Log
import com.google.mediapipe.tasks.genai.llminference.LlmInference
import com.google.mediapipe.tasks.genai.llminference.LlmInference.LlmInferenceOptions
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.withContext
import java.io.File

/**
 * GemmaInference — wraps MediaPipe LiteRT for Gemma 4 E2B-it
 *
 * Target hardware: Snapdragon 732G (Poco X3 NFC)
 * Model: gemma-4-E2B-it-int4 (~1.3 GB)
 * Expected speed: 3–8 tokens/sec on CPU
 */
class GemmaInference(private val context: Context) {

    companion object {
        private const val TAG = "GemmaInference"

        // Model filename — downloaded to internal storage
        const val MODEL_FILENAME = "gemma-4-E2B-it-int4.bin"

        // LiteRT config tuned for Snapdragon 732G
        private const val MAX_TOKENS = 1024
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
    private var isLoaded = false

    /** Path where the model file lives on-device */
    val modelPath: String
        get() = File(context.filesDir, "models/$MODEL_FILENAME").absolutePath

    val modelFile: File
        get() = File(context.filesDir, "models/$MODEL_FILENAME")

    val isModelDownloaded: Boolean
        get() = modelFile.exists() && modelFile.length() > 100_000_000L // > 100 MB sanity check

    val isModelLoaded: Boolean
        get() = isLoaded && llmInference != null

    /**
     * Load the model into memory. Call this once from LuoAiService.
     * Takes ~10–20 seconds on Snapdragon 732G.
     */
    suspend fun loadModel(): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            if (!isModelDownloaded) {
                return@withContext Result.failure(
                    IllegalStateException("Model not downloaded. Call downloadModel() first.")
                )
            }

            Log.i(TAG, "Loading Gemma 4 E2B from $modelPath ...")
            val startMs = System.currentTimeMillis()

            val options = LlmInferenceOptions.builder()
                .setModelPath(modelPath)
                .setMaxTokens(MAX_TOKENS)
                .setTopK(TOP_K)
                .setTemperature(TEMPERATURE)
                .setRandomSeed(RANDOM_SEED)
                // CPU only — Snapdragon 732G has no usable ML NPU via LiteRT
                .setPreferredBackend(LlmInferenceOptions.Backend.CPU)
                .build()

            llmInference = LlmInference.createFromOptions(context, options)
            isLoaded = true

            val elapsed = System.currentTimeMillis() - startMs
            Log.i(TAG, "✓ Gemma 4 E2B loaded in ${elapsed}ms")
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

        val inference = llmInference
            ?: throw IllegalStateException("Model not loaded")

        val prompt = buildPrompt(userMessage, history, tools)
        Log.d(TAG, "Prompt length: ${prompt.length} chars")

        try {
            inference.generateResponseAsync(prompt) { partialResult, done ->
                if (partialResult != null) {
                    trySend(partialResult)
                }
                if (done) {
                    close()
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Generation error", e)
            close(e)
        }

        awaitClose {
            // Flow cancelled — nothing to clean up per-request
        }
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
            val inference = llmInference
                ?: return@withContext Result.failure(IllegalStateException("Model not loaded"))

            val prompt = buildPrompt(userMessage, history, tools)
            val response = inference.generateResponse(prompt)
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
            llmInference?.close()
        } catch (e: Exception) {
            Log.w(TAG, "Error closing LlmInference", e)
        }
        llmInference = null
        isLoaded = false
        Log.i(TAG, "Model unloaded from memory")
    }
}
