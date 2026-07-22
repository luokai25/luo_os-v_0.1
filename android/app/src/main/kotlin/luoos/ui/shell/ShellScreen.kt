package luoos.android.ui.shell

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.launch

private val LuoBlack       = Color(0xFF0A0A0A)
private val LuoDarkSurface = Color(0xFF111111)
private val LuoCard        = Color(0xFF1A1A1A)
private val LuoGreen       = Color(0xFF00FF9F)
private val LuoGreenDim    = Color(0xFF00CC7A)
private val LuoGray        = Color(0xFF666666)
private val LuoWhite       = Color(0xFFE8E8E8)
private val LuoRed         = Color(0xFFFF4444)
private val LuoYellow      = Color(0xFFFFCC00)

@Composable
fun ShellScreen(vm: ShellViewModel = viewModel()) {
    val context   = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val messages  by vm.messages.collectAsState()
    val state     by vm.shellState.collectAsState()
    val inputEnabled by vm.inputEnabled.collectAsState()

    val listState = rememberLazyListState()
    val scope     = rememberCoroutineScope()
    var inputText by remember { mutableStateOf("") }
    val focusRequester = remember { FocusRequester() }

    DisposableEffect(lifecycle) {
        val obs = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> vm.bindService(context)
                Lifecycle.Event.ON_STOP  -> vm.unbindService(context)
                else -> {}
            }
        }
        lifecycle.addObserver(obs)
        onDispose { lifecycle.removeObserver(obs) }
    }

    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            scope.launch { listState.animateScrollToItem(messages.size - 1) }
        }
    }

    Surface(Modifier.fillMaxSize(), color = LuoBlack) {
        Column(Modifier.fillMaxSize()) {
            // Header
            LuoHeader(state) { vm.clearHistory() }

            // Status bar (shown while loading/error)
            if (state !is ShellState.Ready && state !is ShellState.Thinking) {
                LuoStatusBar(state)
            }

            // Message list
            LazyColumn(
                state = listState,
                modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                if (messages.isEmpty()) {
                    item { BootMessage() }
                }
                items(messages, key = { it.id }) { msg ->
                    if (msg.role == "user") UserBubble(msg) else AssistantBubble(msg)
                }
                if (state is ShellState.Thinking && messages.lastOrNull()?.role == "user") {
                    item { ThinkingDots() }
                }
            }

            // Input
            InputBar(
                value    = inputText,
                enabled  = inputEnabled,
                onChange = { inputText = it },
                onSend   = {
                    val t = inputText.trim()
                    if (t.isNotEmpty()) { vm.sendMessage(t); inputText = "" }
                },
                focusRequester = focusRequester
            )
        }
    }
}

@Composable
private fun LuoHeader(state: ShellState, onClear: () -> Unit) {
    val dotColor = when (state) {
        is ShellState.Ready, ShellState.Thinking -> LuoGreen
        is ShellState.LoadingModel               -> LuoYellow
        is ShellState.Error                      -> LuoRed
        else                                     -> LuoGray
    }
    val inf = rememberInfiniteTransition(label = "dot")
    val a by inf.animateFloat(1f, 0.3f,
        infiniteRepeatable(tween(800), RepeatMode.Reverse), label = "a")

    Row(
        Modifier.fillMaxWidth().background(LuoDarkSurface).padding(16.dp, 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(Modifier.size(8.dp)
            .alpha(if (state is ShellState.Ready) 1f else a)
            .background(dotColor, RoundedCornerShape(4.dp)))
        Spacer(Modifier.width(10.dp))
        Text("luo@android", fontFamily = FontFamily.Monospace, fontSize = 15.sp,
             fontWeight = FontWeight.Bold, color = LuoGreen)
        Text(":~\$", fontFamily = FontFamily.Monospace, fontSize = 15.sp, color = LuoGray)
        Spacer(Modifier.weight(1f))
        IconButton(onClick = onClear, modifier = Modifier.size(32.dp)) {
            Icon(Icons.Default.Delete, "Clear", tint = LuoGray, modifier = Modifier.size(18.dp))
        }
    }
}

@Composable
private fun LuoStatusBar(state: ShellState) {
    val (text, color) = when (state) {
        is ShellState.LoadingModel      -> "⏳ Loading Gemma 3 1B..." to LuoYellow
        is ShellState.Extracting        -> "📦 Setting up Luo AI (first launch only)..." to LuoYellow
        is ShellState.ServiceDisconnected -> "🔌 Connecting to AI service..." to LuoGray
        is ShellState.Error             -> "⚠ ${state.message}" to LuoRed
        else                            -> "" to LuoGray
    }
    if (text.isNotEmpty()) {
        Box(Modifier.fillMaxWidth().background(LuoCard).padding(16.dp, 8.dp)) {
            Text(text, fontSize = 12.sp, color = color, fontFamily = FontFamily.Monospace)
        }
    }
}

@Composable
private fun BootMessage() {
    Column(
        Modifier.fillMaxWidth().padding(vertical = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("LUO OS v0.2", fontFamily = FontFamily.Monospace, fontSize = 22.sp,
             fontWeight = FontWeight.Bold, color = LuoGreen)
        Spacer(Modifier.height(4.dp))
        Text("AI is the OS.", fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoGray)
        Spacer(Modifier.height(12.dp))
        Text("Gemma 3 1B · bundled · fully offline",
             fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = Color(0xFF333333))
    }
}

@Composable
private fun UserBubble(msg: ChatMessage) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
        Box(
            Modifier.widthIn(max = 280.dp)
                .background(Color(0xFF1E3A2F), RoundedCornerShape(12.dp, 2.dp, 12.dp, 12.dp))
                .padding(14.dp, 10.dp)
        ) {
            Column {
                Text("> ", fontFamily = FontFamily.Monospace, fontSize = 10.sp, color = LuoGreenDim)
                Text(msg.content, fontSize = 14.sp, color = LuoWhite, lineHeight = 20.sp)
            }
        }
    }
}

@Composable
private fun AssistantBubble(msg: ChatMessage) {
    Column(Modifier.fillMaxWidth()) {
        msg.toolCalls.forEach { call ->
            Text(call, fontFamily = FontFamily.Monospace, fontSize = 11.sp,
                 color = LuoGray, modifier = Modifier.padding(start = 4.dp, bottom = 2.dp))
        }
        Row(verticalAlignment = Alignment.Top) {
            Text("[luo] ", fontFamily = FontFamily.Monospace, fontSize = 11.sp,
                 fontWeight = FontWeight.Bold, color = LuoGreen,
                 modifier = Modifier.padding(top = 2.dp))
            Box(
                Modifier.weight(1f)
                    .background(LuoCard, RoundedCornerShape(2.dp, 12.dp, 12.dp, 12.dp))
                    .padding(14.dp, 10.dp)
            ) {
                Column {
                    Text(msg.content, fontSize = 14.sp, color = LuoWhite, lineHeight = 21.sp)
                    if (msg.isStreaming) {
                        val inf = rememberInfiniteTransition(label = "cursor")
                        val ca by inf.animateFloat(1f, 0f,
                            infiniteRepeatable(tween(500), RepeatMode.Reverse), label = "ca")
                        Text("▌", fontFamily = FontFamily.Monospace, fontSize = 14.sp,
                             color = LuoGreen.copy(alpha = ca))
                    }
                }
            }
        }
    }
}

@Composable
private fun ThinkingDots() {
    val inf = rememberInfiniteTransition(label = "thinking")
    val tick by inf.animateFloat(0f, 3f,
        infiniteRepeatable(tween(900, easing = LinearEasing), RepeatMode.Restart), label = "tick")
    val dots = ".".repeat(tick.toInt() + 1)
    Row(verticalAlignment = Alignment.CenterVertically) {
        Text("[luo] ", fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = LuoGreen)
        Text(dots, fontFamily = FontFamily.Monospace, fontSize = 14.sp, color = LuoGray)
    }
}

@Composable
private fun InputBar(
    value: String, enabled: Boolean,
    onChange: (String) -> Unit, onSend: () -> Unit,
    focusRequester: FocusRequester
) {
    Surface(color = LuoDarkSurface, tonalElevation = 0.dp) {
        Row(
            Modifier.fillMaxWidth().padding(12.dp, 8.dp)
                .navigationBarsPadding().imePadding(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("\$ ", fontFamily = FontFamily.Monospace, fontSize = 16.sp,
                 fontWeight = FontWeight.Bold,
                 color = if (enabled) LuoGreen else LuoGray)
            TextField(
                value = value, onValueChange = onChange,
                modifier = Modifier.weight(1f).focusRequester(focusRequester),
                enabled = enabled,
                placeholder = {
                    Text("ask luo anything...", fontFamily = FontFamily.Monospace,
                         fontSize = 14.sp, color = LuoGray)
                },
                textStyle = TextStyle(fontFamily = FontFamily.Monospace,
                                      fontSize = 14.sp, color = LuoWhite),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor   = Color.Transparent,
                    unfocusedContainerColor = Color.Transparent,
                    disabledContainerColor  = Color.Transparent,
                    focusedIndicatorColor   = Color.Transparent,
                    unfocusedIndicatorColor = Color.Transparent,
                    cursorColor             = LuoGreen
                ),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { onSend() }),
                maxLines = 4
            )
            IconButton(onClick = onSend, enabled = enabled && value.isNotBlank()) {
                Icon(Icons.Default.Send, "Send",
                     tint = if (enabled && value.isNotBlank()) LuoGreen else LuoGray)
            }
        }
    }
}
