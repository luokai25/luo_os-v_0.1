package luoos.android.ui.apps

import android.os.Environment
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import luoos.android.ui.theme.LuoColors
import java.text.SimpleDateFormat
import java.util.*

/**
 * TerminalScreen — a small set of real, useful built-in commands
 * (help, time, storage, ls, clear), styled as a plain command line.
 * Not a full shell/POSIX emulator — that's a much larger undertaking;
 * this ships genuinely working commands for real device information
 * rather than a cosmetic prompt that does nothing.
 */
@Composable
fun TerminalScreen() {
    var lines by remember { mutableStateOf(listOf("Luo OS terminal — type 'help' for commands")) }
    var input by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()

    fun run(command: String) {
        val trimmed = command.trim()
        if (trimmed.isEmpty()) return

        lines = lines + "$ $trimmed"

        val output = when (trimmed.lowercase().substringBefore(" ")) {
            "help" -> listOf(
                "Available commands:",
                "  help      show this list",
                "  time      current date and time",
                "  storage   internal/external storage usage",
                "  ls        list files in external storage root",
                "  clear     clear the screen"
            )
            "time" -> listOf(
                SimpleDateFormat("EEEE, MMMM d yyyy — HH:mm:ss", Locale.getDefault()).format(Date())
            )
            "storage" -> {
                val dataDir = Environment.getDataDirectory()
                val extDir = Environment.getExternalStorageDirectory()
                listOf(
                    "Internal: ${formatBytes(dataDir.totalSpace - dataDir.freeSpace)} used / ${formatBytes(dataDir.totalSpace)} total",
                    "External: ${formatBytes(extDir.totalSpace - extDir.freeSpace)} used / ${formatBytes(extDir.totalSpace)} total"
                )
            }
            "ls" -> {
                val dir = Environment.getExternalStorageDirectory()
                dir.listFiles()?.take(30)?.map { f ->
                    val marker = if (f.isDirectory) "d" else "-"
                    "$marker  ${f.name}"
                } ?: listOf("(cannot read directory)")
            }
            "clear" -> {
                lines = emptyList()
                return
            }
            else -> listOf("Unknown command: '$trimmed' — type 'help' for the list")
        }

        lines = lines + output
    }

    Column(Modifier.fillMaxSize().background(LuoColors.terminalBackground)) {
        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(12.dp)
        ) {
            items(lines) { line ->
                Text(
                    line,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 13.sp,
                    color = LuoColors.terminalText,
                    lineHeight = 19.sp
                )
            }
        }

        LaunchedEffect(lines.size) {
            if (lines.isNotEmpty()) {
                scope.launch { listState.animateScrollToItem(lines.size - 1) }
            }
        }

        Row(
            Modifier.fillMaxWidth().padding(10.dp).imePadding().navigationBarsPadding(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("$ ", fontFamily = FontFamily.Monospace, fontSize = 15.sp, color = LuoColors.terminalText)
            TextField(
                value = input,
                onValueChange = { input = it },
                modifier = Modifier.weight(1f),
                textStyle = TextStyle(
                    fontFamily = FontFamily.Monospace, fontSize = 14.sp, color = LuoColors.terminalText
                ),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
                    unfocusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
                    focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    cursorColor = LuoColors.terminalText
                ),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = {
                    run(input)
                    input = ""
                }),
                singleLine = true
            )
            IconButton(onClick = { run(input); input = "" }) {
                Icon(Icons.Default.Send, "Run", tint = LuoColors.terminalText)
            }
        }
    }
}

private fun formatBytes(bytes: Long): String = when {
    bytes >= 1_073_741_824 -> "%.1f GB".format(bytes / 1_073_741_824.0)
    bytes >= 1_048_576     -> "%.1f MB".format(bytes / 1_048_576.0)
    else                   -> "$bytes B"
}
