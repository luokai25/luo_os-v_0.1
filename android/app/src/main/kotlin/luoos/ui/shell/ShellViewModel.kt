package luoos.android.ui.shell

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.os.IBinder
import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import luoos.android.ai.AgentEvent
import luoos.android.ai.LuoAiService
import luoos.android.models.LuoChatMessage

data class ChatMessage(
    val id: Long = System.currentTimeMillis(),
    val role: String,           // "user" | "assistant"
    val content: String,
    val isStreaming: Boolean = false,
    val toolCalls: List<String> = emptyList(),
    // Real reasoning trace for this message, shown as collapsible "thoughts"
    // in the UI — one entry per ReAct iteration's Thought: line, plus an
    // optional leading Plan entry. Empty for plain (non-agentic) responses.
    val thoughts: List<String> = emptyList()
)

sealed class ShellState {
    object ServiceDisconnected : ShellState()
    object Extracting : ShellState()
    object LoadingModel : ShellState()
    object Ready : ShellState()
    object Thinking : ShellState()
    data class Error(val message: String) : ShellState()
}

class ShellViewModel : ViewModel() {

    companion object {
        private const val TAG = "ShellViewModel"
    }

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages

    private val _shellState = MutableStateFlow<ShellState>(ShellState.ServiceDisconnected)
    val shellState: StateFlow<ShellState> = _shellState

    private val _inputEnabled = MutableStateFlow(false)
    val inputEnabled: StateFlow<Boolean> = _inputEnabled

    // Conversation history for the model (user/assistant pairs)
    private val conversationHistory = mutableListOf<Pair<String, String>>()

    private var luoService: LuoAiService? = null

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            Log.d(TAG, "Service connected")
            val service = (binder as LuoAiService.LuoBinder).getService()
            luoService = service

            // Observe service state
            viewModelScope.launch {
                service.state.collect { serviceState ->
                    _shellState.value = when (serviceState) {
                        is LuoAiService.ServiceState.Idle -> ShellState.LoadingModel
                        is LuoAiService.ServiceState.Extracting -> ShellState.Extracting
                        is LuoAiService.ServiceState.LoadingModel -> ShellState.LoadingModel
                        is LuoAiService.ServiceState.Ready -> {
                            _inputEnabled.value = true
                            ShellState.Ready
                        }
                        is LuoAiService.ServiceState.Error -> {
                            _inputEnabled.value = false
                            ShellState.Error(serviceState.message)
                        }
                    }
                }
            }
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            Log.w(TAG, "Service disconnected")
            luoService = null
            _shellState.value = ShellState.ServiceDisconnected
            _inputEnabled.value = false
        }
    }

    fun bindService(context: Context) {
        val intent = LuoAiService.startIntent(context)
        context.startForegroundService(intent)
        context.bindService(
            Intent(context, LuoAiService::class.java),
            serviceConnection,
            Context.BIND_AUTO_CREATE
        )
    }

    fun unbindService(context: Context) {
        try { context.unbindService(serviceConnection) } catch (_: Exception) {}
    }

    fun sendMessage(userText: String) {
        if (userText.isBlank()) return
        val service = luoService ?: return

        // Add user message to UI
        val userMsg = ChatMessage(role = "user", content = userText.trim())
        _messages.value = _messages.value + userMsg

        // Add placeholder for the assistant's response. Since LuoAgent's
        // ReAct loop calls llama.cpp non-streaming per-iteration (see
        // LlamaInference.generate's doc comment), there's no token-by-token
        // stream anymore — instead this placeholder fills in with each real
        // Thought as it arrives, then the Final Answer once the loop
        // completes. This is more honest than the old word-chunked fake
        // streaming: what's shown IS the model's real reasoning trace.
        val assistantPlaceholder = ChatMessage(
            id = System.currentTimeMillis() + 1,
            role = "assistant",
            content = "",
            isStreaming = true
        )
        _messages.value = _messages.value + assistantPlaceholder

        _inputEnabled.value = false
        _shellState.value = ShellState.Thinking

        viewModelScope.launch {
            val toolCallsList = mutableListOf<String>()
            val thoughtsList = mutableListOf<String>()

            service.agent.process(userText.trim(), conversationHistory.toList())
                .collect { event ->
                    when (event) {
                        is AgentEvent.Thinking -> {
                            // already set state above
                        }
                        is AgentEvent.Plan -> {
                            thoughtsList.add("Plan:\n${event.planText}")
                            _messages.value = _messages.value.dropLast(1) + assistantPlaceholder.copy(
                                thoughts = thoughtsList.toList(),
                                isStreaming = true
                            )
                        }
                        is AgentEvent.ThoughtStep -> {
                            thoughtsList.add(event.text)
                            // Show the latest thought as the live "typing"
                            // content — the user sees real reasoning happen,
                            // not a placeholder spinner.
                            _messages.value = _messages.value.dropLast(1) + assistantPlaceholder.copy(
                                content = event.text,
                                thoughts = thoughtsList.toList(),
                                isStreaming = true
                            )
                        }
                        is AgentEvent.ToolCall -> {
                            toolCallsList.add("⚙ ${event.toolName}(${event.paramsRaw.take(60)})")
                            _messages.value = _messages.value.dropLast(1) + assistantPlaceholder.copy(
                                toolCalls = toolCallsList.toList(),
                                thoughts = thoughtsList.toList(),
                                isStreaming = true
                            )
                        }
                        is AgentEvent.ToolResult -> {
                            toolCallsList.add("✓ ${event.toolName}: ${event.result.take(80)}")
                            _messages.value = _messages.value.dropLast(1) + assistantPlaceholder.copy(
                                toolCalls = toolCallsList.toList(),
                                thoughts = thoughtsList.toList(),
                                isStreaming = true
                            )
                        }
                        is AgentEvent.Done -> {
                            // Finalize the assistant message
                            _messages.value = _messages.value.dropLast(1) + assistantPlaceholder.copy(
                                content = event.fullResponse.trim(),
                                isStreaming = false,
                                toolCalls = toolCallsList.toList(),
                                thoughts = thoughtsList.toList()
                            )
                            // Update conversation history
                            conversationHistory.add(Pair("user", userText.trim()))
                            conversationHistory.add(Pair("assistant", event.fullResponse.trim()))
                            // Keep history manageable
                            while (conversationHistory.size > 20) {
                                conversationHistory.removeAt(0)
                                conversationHistory.removeAt(0)
                            }
                            _inputEnabled.value = true
                            _shellState.value = ShellState.Ready
                        }
                        is AgentEvent.Error -> {
                            _messages.value = _messages.value.dropLast(1) + assistantPlaceholder.copy(
                                content = "⚠ ${event.message}",
                                isStreaming = false,
                                thoughts = thoughtsList.toList()
                            )
                            _inputEnabled.value = true
                            _shellState.value = ShellState.Ready
                        }
                    }
                }
        }
    }

    fun clearHistory() {
        _messages.value = emptyList()
        conversationHistory.clear()
    }
}
