package luoos.android.ai

import android.util.Log
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * LuoAgent — the autonomous agent loop for Luo OS, ported from the laptop
 * OS's real react_agent.py (ReActAgent class) rather than the simplified
 * single-JSON-tool-call loop this file used before.
 *
 * Real ReAct loop, matching the laptop exactly:
 *   Question: <user input>
 *   Thought: <reasoning>
 *   Action: <tool name>
 *   Action Input: <JSON params>
 *   Observation: <tool result>
 *   ... (repeat) ...
 *   Thought: <final reasoning>
 *   Final Answer: <response to user>
 *
 * The whole scratchpad (not just the latest turn) is re-sent to the model
 * on every iteration, exactly like react_agent.py's `"\n".join(scratchpad)`
 * — this is what lets the model's later Thoughts build on its own earlier
 * reasoning instead of starting fresh each time.
 *
 * Two real behavioral differences from the laptop, both deliberate and
 * both aimed at a 1.5B model on a phone's constrained context window:
 *   - MAX_ITERATIONS is 6 here vs the laptop's 10. Each iteration re-sends
 *     the whole scratchpad, so iteration count directly drives token/
 *     compute cost — see LuoModelStats for the actual measured cost.
 *   - Tool descriptions use LuoTools.toPromptDescription()'s compact
 *     "- name (params): desc" format, matching the laptop's real
 *     _get_tools_description(), not the old verbose JSON-schema format
 *     this file used to send.
 */
class LuoAgent(
    private val llama: LlamaInference,
    private val tools: LuoTools
) {
    companion object {
        private const val TAG = "LuoAgent"
        private const val MAX_ITERATIONS = 6

        // Same regex shapes as react_agent.py's _parse_thought_action,
        // translated to Kotlin's Regex syntax.
        private val THOUGHT_REGEX = Regex("""Thought:\s*(.+?)(?=Action:|Final Answer:|$)""", RegexOption.DOT_MATCHES_ALL)
        private val ACTION_REGEX  = Regex("""Action:\s*(\w+)""")
        private val ACTION_INPUT_REGEX = Regex("""Action Input:\s*(\{.+?\}|\S+)""", RegexOption.DOT_MATCHES_ALL)
        private val FINAL_ANSWER_REGEX = Regex("""Final Answer:\s*(.+)""", RegexOption.DOT_MATCHES_ALL)

        // Keyword heuristics matching react_agent.py's _needs_planning —
        // decides whether to run a short planning pass before the ReAct
        // loop, for tasks that sound genuinely multi-step.
        private val PLANNING_KEYWORDS = listOf(
            "plan", "create", "build", "implement", "develop", "design",
            "multiple", "steps", "comprehensive", "complete", "full",
            "and then", "followed by", "after that", "sequence",
            "project", "application", "system", "architecture"
        )

        private fun needsPlanning(userInput: String): Boolean {
            val lower = userInput.lowercase()
            return PLANNING_KEYWORDS.any { lower.contains(it) } && userInput.split(" ").size > 10
        }
    }

    /**
     * Process a user message through the full ReAct agent pipeline.
     * Emits a Flow of AgentEvent — Thought events let the UI genuinely show
     * the model's reasoning trace (see AgentEvent.ThoughtStep), not just the
     * final text.
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

        // Optional planning pass for tasks that sound genuinely multi-step —
        // matches react_agent.py's _needs_planning gate. Skipped for
        // ordinary chat/simple requests so a plain "hi" doesn't pay for an
        // extra generation call it doesn't need.
        var planText: String? = null
        if (needsPlanning(userMessage)) {
            Log.d(TAG, "Task looks multi-step, running planning pass")
            val planResult = llama.generate(
                userMessage = "Task: $userMessage",
                history = emptyList(),
                systemPrompt = LuoPrompts.SYSTEM_PROMPT_PLANNING
            )
            planResult.getOrNull()?.let { generation ->
                LuoModelStats.recordGeneration(generation)
                planText = generation.text
                emit(AgentEvent.Plan(generation.text))
            }
        }

        val toolsDescription = tools.toPromptDescription()
        val systemPrompt = LuoPrompts.buildReactPrompt(toolsDescription)

        // The scratchpad accumulates the whole reasoning trace for this
        // turn — exactly like react_agent.py's `scratchpad` list, joined
        // with "\n" and re-sent on every iteration.
        val scratchpad = StringBuilder("Question: $userMessage")
        if (planText != null) {
            scratchpad.append("\nPlan:\n$planText")
        }

        var iteration = 0
        var finalAnswer: String? = null

        while (iteration < MAX_ITERATIONS) {
            iteration++
            Log.d(TAG, "ReAct iteration $iteration")

            val thoughtPrompt = "$scratchpad\nThought:"
            val generation = llama.generate(
                userMessage = thoughtPrompt,
                history = history,
                systemPrompt = systemPrompt
            ).getOrElse { e ->
                Log.e(TAG, "Generation failed", e)
                emit(AgentEvent.Error("Generation failed: ${e.message}"))
                return@flow
            }
            LuoModelStats.recordGeneration(generation)
            val response = generation.text

            // Final Answer short-circuits the loop immediately — matches
            // react_agent.py checking for it before doing anything else
            // with the response.
            val finalMatch = FINAL_ANSWER_REGEX.find(response)
            if (finalMatch != null) {
                finalAnswer = finalMatch.groupValues[1].trim()
                val thoughtBeforeFinal = THOUGHT_REGEX.find(response)?.groupValues?.get(1)?.trim()
                if (!thoughtBeforeFinal.isNullOrBlank()) {
                    emit(AgentEvent.ThoughtStep(iteration, thoughtBeforeFinal))
                }
                break
            }

            val thought = THOUGHT_REGEX.find(response)?.groupValues?.get(1)?.trim().orEmpty()
            val actionName = ACTION_REGEX.find(response)?.groupValues?.get(1)
            val actionInputRaw = ACTION_INPUT_REGEX.find(response)?.groupValues?.get(1)

            if (thought.isNotBlank()) {
                emit(AgentEvent.ThoughtStep(iteration, thought))
            }
            scratchpad.append("\nThought: $thought")

            if (actionName == null) {
                // No Action and no Final Answer — the model produced a plain
                // response. Treat it as the final answer rather than loop
                // again on a malformed turn (a real, if rare, LLM failure
                // mode worth handling gracefully instead of burning another
                // full generation call on a 1.5B model).
                finalAnswer = if (thought.isNotBlank()) thought else response.trim()
                break
            }

            emit(AgentEvent.ToolCall(actionName, actionInputRaw ?: "{}"))

            val actionInputJson: JsonObject = try {
                if (actionInputRaw != null && actionInputRaw.trim().startsWith("{")) {
                    JsonParser.parseString(actionInputRaw).asJsonObject
                } else {
                    JsonObject()
                }
            } catch (e: Exception) {
                Log.w(TAG, "Could not parse Action Input as JSON: $actionInputRaw", e)
                JsonObject()
            }

            val observation = try {
                tools.execute(actionName, actionInputJson)
            } catch (e: Exception) {
                Log.e(TAG, "Tool execution error", e)
                "ERROR: ${e.message}"
            }

            val truncatedObservation = observation.take(500) // matches react_agent.py's [:500]
            emit(AgentEvent.ToolResult(actionName, truncatedObservation))

            scratchpad.append("\nAction: $actionName")
            scratchpad.append("\nAction Input: $actionInputRaw")
            scratchpad.append("\nObservation: $truncatedObservation")
        }

        if (finalAnswer == null) {
            Log.w(TAG, "Hit max ReAct iterations ($MAX_ITERATIONS) without a Final Answer")
            emit(AgentEvent.Error("Agent reached maximum reasoning steps. Please try rephrasing."))
            return@flow
        }

        val updatedHistory = history + Pair("user", userMessage) + Pair("assistant", finalAnswer)
        emit(AgentEvent.Done(finalAnswer, updatedHistory))
    }
}

// ─── Agent Events (sealed class for UI) ──────────────────────────────────────

sealed class AgentEvent {
    /** Model is starting to think */
    object Thinking : AgentEvent()

    /** A short numbered plan produced by the planning pass, before the ReAct loop starts */
    data class Plan(val planText: String) : AgentEvent()

    /**
     * One real reasoning step — the model's own "Thought:" text for a given
     * iteration. This is what lets the UI show genuine chain-of-thought
     * rather than just the final answer, matching the laptop's Thought
     * dataclass (react_agent.py) conceptually, though this Android version
     * carries only what the UI needs (iteration + text) rather than the
     * laptop's full confidence/importance/embedding fields.
     */
    data class ThoughtStep(val iteration: Int, val text: String) : AgentEvent()

    /** Model decided to call a tool */
    data class ToolCall(val toolName: String, val paramsRaw: String) : AgentEvent()

    /** Tool finished executing */
    data class ToolResult(val toolName: String, val result: String) : AgentEvent()

    /** Final response ready, agent loop complete */
    data class Done(val fullResponse: String, val updatedHistory: List<Pair<String, String>>) : AgentEvent()

    /** Something went wrong */
    data class Error(val message: String) : AgentEvent()
}
