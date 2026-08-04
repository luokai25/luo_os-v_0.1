package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Save
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors
import java.io.File

/**
 * CodeScreen — a plain-text code editor over files in the app's own
 * storage. No syntax highlighting yet (that's a real, separate feature —
 * a tokenizer/highlighter per language — worth adding once basic editing
 * is confirmed useful); this ships genuine open/edit/save rather than a
 * cosmetic text box.
 */
@Composable
fun CodeScreen() {
    val context = LocalContext.current
    val codeDir = remember { File(context.filesDir, "code").apply { mkdirs() } }

    var currentFile by remember { mutableStateOf<File?>(null) }
    var content by remember { mutableStateOf("") }
    var fileNameInput by remember { mutableStateOf("") }
    var showNewFileDialog by remember { mutableStateOf(false) }

    val files = remember(currentFile) {
        codeDir.listFiles()?.filter { it.isFile }?.sortedBy { it.name } ?: emptyList()
    }

    val openFile = currentFile
    if (openFile == null) {
        CodeFileList(
            files = files,
            onOpen = { file -> currentFile = file; content = file.readText() },
            onNewFile = { showNewFileDialog = true }
        )
        if (showNewFileDialog) {
            NewFileDialog(
                nameInput = fileNameInput,
                onNameChange = { fileNameInput = it },
                onDismiss = { showNewFileDialog = false },
                onCreate = {
                    if (fileNameInput.isNotBlank()) {
                        val newFile = File(codeDir, fileNameInput.trim())
                        newFile.writeText("")
                        currentFile = newFile
                        content = ""
                        fileNameInput = ""
                        showNewFileDialog = false
                    }
                }
            )
        }
    } else {
        CodeEditor(
            fileName = openFile.name,
            content = content,
            onContentChange = { content = it },
            onBack = { currentFile = null },
            onSave = { openFile.writeText(content) }
        )
    }
}

@Composable
private fun CodeFileList(files: List<File>, onOpen: (File) -> Unit, onNewFile: () -> Unit) {
    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        Row(
            Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Code", fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
                 fontSize = 20.sp, color = LuoColors.textBright)
            Spacer(Modifier.weight(1f))
            TextButton(onClick = onNewFile) {
                Text("+ New", fontFamily = FontFamily.Monospace, color = LuoColors.accent)
            }
        }

        if (files.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No files yet — tap + New to create one",
                     fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textDim)
            }
        } else {
            LazyColumn(Modifier.fillMaxSize().padding(horizontal = 12.dp)) {
                items(files) { file ->
                    Text(
                        file.name,
                        fontFamily = FontFamily.Monospace, fontSize = 14.sp, color = LuoColors.textNormal,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onOpen(file) }
                            .padding(vertical = 10.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun NewFileDialog(
    nameInput: String,
    onNameChange: (String) -> Unit,
    onDismiss: () -> Unit,
    onCreate: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = LuoColors.card,
        title = { Text("New file", fontFamily = FontFamily.Monospace, color = LuoColors.textBright) },
        text = {
            TextField(
                value = nameInput,
                onValueChange = onNameChange,
                placeholder = { Text("filename.kt", fontFamily = FontFamily.Monospace, color = LuoColors.textDim) },
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = LuoColors.cardAlt,
                    unfocusedContainerColor = LuoColors.cardAlt,
                    focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    cursorColor = LuoColors.accent
                )
            )
        },
        confirmButton = {
            TextButton(onClick = onCreate) { Text("Create", color = LuoColors.accent, fontFamily = FontFamily.Monospace) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel", color = LuoColors.textDim, fontFamily = FontFamily.Monospace) }
        }
    )
}

@Composable
private fun CodeEditor(
    fileName: String,
    content: String,
    onContentChange: (String) -> Unit,
    onBack: () -> Unit,
    onSave: () -> Unit
) {
    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        Row(
            Modifier.fillMaxWidth().padding(12.dp, 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextButton(onClick = onBack) { Text("← Files", fontFamily = FontFamily.Monospace, color = LuoColors.accent) }
            Spacer(Modifier.weight(1f))
            Text(fileName, fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textDim)
            Spacer(Modifier.weight(1f))
            IconButton(onClick = onSave) { Icon(Icons.Default.Save, "Save", tint = LuoColors.accent) }
        }

        TextField(
            value = content,
            onValueChange = onContentChange,
            modifier = Modifier.fillMaxSize().padding(horizontal = 8.dp),
            textStyle = TextStyle(fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textNormal, lineHeight = 19.sp),
            colors = TextFieldDefaults.colors(
                focusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
                unfocusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
                focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                cursorColor = LuoColors.accent
            )
        )
    }
}
