package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors
import java.text.SimpleDateFormat
import java.util.*

data class LuoNote(
    val id: Long = System.currentTimeMillis(),
    var title: String,
    var body: String,
    val createdAt: Long = System.currentTimeMillis()
)

/**
 * NotesScreen — a plain, local (in-memory for now) note list + editor.
 * Persisting notes to Room is a reasonable next step once this needs to
 * survive app restarts; kept in-memory here to ship a working screen first.
 */
@Composable
fun NotesScreen() {
    var notes by remember { mutableStateOf(listOf<LuoNote>()) }
    var openNote by remember { mutableStateOf<LuoNote?>(null) }

    val current = openNote
    if (current != null) {
        NoteEditor(
            note = current,
            onBack = { openNote = null },
            onSave = { updated ->
                notes = notes.map { if (it.id == updated.id) updated else it }
                openNote = null
            },
            onDelete = { toDelete ->
                notes = notes.filterNot { it.id == toDelete.id }
                openNote = null
            }
        )
    } else {
        NoteList(
            notes = notes,
            onOpen = { openNote = it },
            onNew = {
                val note = LuoNote(title = "", body = "")
                notes = listOf(note) + notes
                openNote = note
            }
        )
    }
}

@Composable
private fun NoteList(notes: List<LuoNote>, onOpen: (LuoNote) -> Unit, onNew: () -> Unit) {
    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        Row(
            Modifier.fillMaxWidth().padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Notes", fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
                 fontSize = 20.sp, color = LuoColors.textBright)
            Spacer(Modifier.weight(1f))
            IconButton(onClick = onNew) {
                Icon(Icons.Default.Add, "New note", tint = LuoColors.accent)
            }
        }

        if (notes.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No notes yet — tap + to add one",
                     fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textDim)
            }
        } else {
            LazyColumn(
                Modifier.fillMaxSize().padding(horizontal = 12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(notes, key = { it.id }) { note ->
                    NoteRow(note = note, onClick = { onOpen(note) })
                }
            }
        }
    }
}

@Composable
private fun NoteRow(note: LuoNote, onClick: () -> Unit) {
    val dateStr = remember(note.createdAt) {
        SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(Date(note.createdAt))
    }
    Column(
        Modifier
            .fillMaxWidth()
            .background(LuoColors.card, RoundedCornerShape(10.dp))
            .clickable(onClick = onClick)
            .padding(14.dp)
    ) {
        Text(
            note.title.ifBlank { "Untitled" },
            fontFamily = FontFamily.Monospace, fontWeight = FontWeight.SemiBold,
            fontSize = 15.sp, color = LuoColors.textBright, maxLines = 1
        )
        Spacer(Modifier.height(4.dp))
        Text(
            note.body.ifBlank { "No content" },
            fontFamily = FontFamily.Monospace, fontSize = 12.sp,
            color = LuoColors.textDim, maxLines = 2
        )
        Spacer(Modifier.height(4.dp))
        Text(dateStr, fontFamily = FontFamily.Monospace, fontSize = 10.sp, color = LuoColors.textFaint)
    }
}

@Composable
private fun NoteEditor(
    note: LuoNote,
    onBack: () -> Unit,
    onSave: (LuoNote) -> Unit,
    onDelete: (LuoNote) -> Unit
) {
    var title by remember { mutableStateOf(note.title) }
    var body by remember { mutableStateOf(note.body) }

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        Row(
            Modifier.fillMaxWidth().padding(8.dp, 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = { onSave(note.copy(title = title, body = body)) }) {
                Icon(Icons.Default.ArrowBack, "Save and back", tint = LuoColors.accent)
            }
            Spacer(Modifier.weight(1f))
            IconButton(onClick = { onDelete(note) }) {
                Icon(Icons.Default.Delete, "Delete note", tint = LuoColors.statusBad)
            }
        }

        TextField(
            value = title,
            onValueChange = { title = it },
            placeholder = { Text("Title", fontFamily = FontFamily.Monospace, color = LuoColors.textDim) },
            textStyle = androidx.compose.ui.text.TextStyle(
                fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
                fontSize = 18.sp, color = LuoColors.textBright
            ),
            colors = noteFieldColors(),
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp),
            singleLine = true
        )

        TextField(
            value = body,
            onValueChange = { body = it },
            placeholder = { Text("Start writing...", fontFamily = FontFamily.Monospace, color = LuoColors.textDim) },
            textStyle = androidx.compose.ui.text.TextStyle(
                fontFamily = FontFamily.Monospace, fontSize = 14.sp, color = LuoColors.textNormal, lineHeight = 20.sp
            ),
            colors = noteFieldColors(),
            modifier = Modifier.fillMaxSize().padding(horizontal = 12.dp)
        )
    }
}

@Composable
private fun noteFieldColors() = TextFieldDefaults.colors(
    focusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
    unfocusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
    focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
    unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
    cursorColor = LuoColors.accent
)
