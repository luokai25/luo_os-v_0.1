package luoos.android.ai

import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * LuoAgent — the autonomous agent loop for Luo OS.
 *
 * Implements:
 *  1. Simple chat mode (user ↔ Gemma)
 *  2. Agent mode: detect tool calls in model output → execute → feed result back
 *
 * Gemma 3 1B-IT signals tool calls via JSON blocks:
 *  {"tool": "tool_name", "params": {...}}
 *
 * The agent keeps looping (max 5 iterations) until the model stops calling tools
 * and produces a final natural language response.
 */
class LuoAgent(
    private val gemma: GemmaInference,
    private val tools: LuoTools
) {
    companion object {
        private const val TAG = "LuoAgent"
        private const val MAX_AGENT_ITERATIONS = 5
        private val TOOL_CALL_REGEX = Regex(
            """\{"tool"\s*:\s*"([^"]+)"\s*,\s*"params"\s*:\s*(\{[^}]*\})\}""",
            RegexOption.DOT_MATCHES_ALL
        )
    }

    private val gson = Gson()

    /**
     * Process a user message through the full agent pipeline.
     * Emits a Flow of AgentEvent so the UI can stream tokens live
     * and show tool execution inline.
     */
    fun process(
        userMessage: String,
        history: List<Pair<String, String>>
    ): Flow<AgentEvent> = flow {

        if (!gemma.isModelLoaded) {
            emit(AgentEvent.Error("Gemma model is not loaded yet."))
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

            // Collect the full model response (need full text to detect tool calls)
            val responseBuilder = StringBuilder()

            // Stream tokens to UI as they arrive
            gemma.generateStreaming(userInput, currentHistory, toolsJson)
                .collect { token ->
                    responseBuilder.append(token)
                    emit(AgentEvent.Token(token))
                }

            val fullResponse = responseBuilder.toString()
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
