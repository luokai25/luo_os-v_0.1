package luoos.android.ai

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * LuoAgent — the autonomous agent loop for Luo OS.
 *
 * Implements:
 *  1. Simple chat mode (user ↔ Qwen2.5-1.5B via llama.cpp)
 *  2. Agent mode: detect tool calls in model output → execute → feed result back
 *
 * The model signals tool calls via JSON blocks:
 *  {"tool": "tool_name", "params": {...}}
 *
 * The agent keeps looping (max 5 iterations) until the model stops calling tools
 * and produces a final natural language response.
 *
 * NOTE: llama.cpp is called here via LlamaInference.generate(), which returns
 * a complete response rather than a token Flow (unlike the earlier MediaPipe-
 * based GemmaInference.generateStreaming()). The response is chunked into
 * words with a small delay to preserve a similar "typing" feel in the UI —
 * an honest approximation, not real token-by-token streaming. A true native
 * streaming callback is a reasonable future improvement (see
 * luoos_llama_jni.cpp's nativeGenerate doc comment) but isn't required for
 * correctness.
 */
class LuoAgent(
    private val llama: LlamaInference,
    private val tools: LuoTools
) {
    companion object {
        private const val TAG = "LuoAgent"
        private const val MAX_AGENT_ITERATIONS = 5
        private const val WORD_CHUNK_DELAY_MS = 30L
        private val TOOL_CALL_REGEX = Regex(
            """\{"tool"\s*:\s*"([^"]+)"\s*,\s*"params"\s*:\s*(\{[^}]*\})\}""",
            RegexOption.DOT_MATCHES_ALL
        )
    }

    private val gson = Gson()

    /**
     * Process a user message through the full agent pipeline.
     * Emits a Flow of AgentEvent so the UI can display a typing-like effect
     * and show tool execution inline.
     */
    fun process(
        userMessage: String,
        history: List<Pair<String, String>>
    ): Flow<AgentEvent> = flow {

        if (!llama.isModelLoaded) {
            emit(AgentEvent.Error("Model is not loaded yet."))
            return@flow
        }

        emit(AgentEvent.Thinking)

        val toolsJson = tools.toPromptJson()
        var currentHistory = history.toMutableList()
        var userInput = userMessage
        var iterations = 0

        while (iterations < MAX_AGENT_ITERATIONS) {
            iterations++
            Log.d(TAG, "Agent iteration $iterations for: $userInput")

            // llama.cpp returns the full response in one call (see class doc
            // comment) — chunk it into words to emit a typing-like effect.
            val fullResponse = llama.generate(userInput, currentHistory, toolsJson)
                .getOrElse { e ->
                    Log.e(TAG, "Generation failed", e)
                    emit(AgentEvent.Error("Generation failed: ${e.message}"))
                    return@flow
                }

            val words = fullResponse.split(" ")
            for ((index, word) in words.withIndex()) {
                val chunk = if (index == 0) word else " $word"
                emit(AgentEvent.Token(chunk))
                delay(WORD_CHUNK_DELAY_MS)
            }

            Log.d(TAG, "Model response: ${fullResponse.take(200)}...")

            // Check if the model wants to call a tool
            val toolMatch = TOOL_CALL_REGEX.find(fullResponse)

            if (toolMatch == null) {
                // No tool call — this is the final response
                currentHistory.add(Pair("user", userInput))
                currentHistory.add(Pair("assistant", fullResponse))
                emit(AgentEvent.Done(fullResponse, currentHistory))
                return@flow
            }

            // Tool call detected
            val toolName = toolMatch.groupValues[1]
            val paramsStr = toolMatch.groupValues[2]

            Log.d(TAG, "Tool call detected: $toolName($paramsStr)")
            emit(AgentEvent.ToolCall(toolName, paramsStr))

            // Execute the tool
            val toolResult = try {
                val params = JsonParser.parseString(paramsStr).asJsonObject
                tools.execute(toolName, params)
            } catch (e: Exception) {
                Log.e(TAG, "Tool parse/execute error", e)
                "ERROR: Could not execute tool: ${e.message}"
            }

            Log.d(TAG, "Tool result: ${toolResult.take(100)}")
            emit(AgentEvent.ToolResult(toolName, toolResult))

            // Feed tool result back to model
            currentHistory.add(Pair("user", userInput))
            currentHistory.add(Pair("assistant", fullResponse))
            userInput = "Tool '$toolName' returned:\n$toolResult\n\nNow please respond to the user based on this result."
        }

        // Hit max iterations
        Log.w(TAG, "Hit max agent iterations ($MAX_AGENT_ITERATIONS)")
        emit(AgentEvent.Error("Agent reached maximum steps. Please try rephrasing."))
    }
}

// ─── Agent Events (sealed class for UI) ──────────────────────────────────────

sealed class AgentEvent {
    /** Model is starting to think */
    object Thinking : AgentEvent()

    /** A new token streamed from the model */
    data class Token(val text: String) : AgentEvent()

    /** Model decided to call a tool */
    data class ToolCall(val toolName: String, val params: String) : AgentEvent()

    /** Tool finished executing */
    data class ToolResult(val toolName: String, val result: String) : AgentEvent()

    /** Final response ready, agent loop complete */
    data class Done(val fullResponse: String, val updatedHistory: List<Pair<String, String>>) : AgentEvent()

    /** Something went wrong */
    data class Error(val message: String) : AgentEvent()
}

