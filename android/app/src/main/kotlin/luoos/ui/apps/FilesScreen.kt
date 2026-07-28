package luoos.android.ui.apps

import android.os.Environment
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors
import java.io.File

/**
 * FilesScreen — a real browser over the device's own storage, starting at
 * the external storage root. Read-only for now (no move/delete/rename);
 * those are reasonable next additions once basic browsing is confirmed
 * working well.
 */
@Composable
fun FilesScreen() {
    val rootDir = remember { Environment.getExternalStorageDirectory() }
    var currentDir by remember { mutableStateOf(rootDir) }

    val entries = remember(currentDir) {
        currentDir.listFiles()
            ?.sortedWith(compareBy({ !it.isDirectory }, { it.name.lowercase() }))
            ?: emptyList()
    }

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        // Header with path + back button
        Row(
            Modifier.fillMaxWidth().padding(12.dp, 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (currentDir != rootDir) {
                IconButton(onClick = { currentDir = currentDir.parentFile ?: rootDir }) {
                    Icon(Icons.Default.ArrowBack, "Up one level", tint = LuoColors.accent)
                }
            }
            Text(
                currentDir.path.removePrefix(rootDir.path).ifEmpty { "/" },
                fontFamily = FontFamily.Monospace, fontSize = 13.sp,
                color = LuoColors.textDim, maxLines = 1
            )
        }

        if (entries.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("Empty folder", fontFamily = FontFamily.Monospace,
                     fontSize = 13.sp, color = LuoColors.textDim)
            }
        } else {
            LazyColumn(Modifier.fillMaxSize()) {
                items(entries, key = { it.absolutePath }) { entry ->
                    FileRow(entry = entry, onClick = {
                        if (entry.isDirectory) currentDir = entry
                        // Tapping a plain file currently does nothing further —
                        // opening file contents with the right viewer per type
                        // is a reasonable next addition.
                    })
                }
            }
        }
    }
}

@Composable
private fun FileRow(entry: File, onClick: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(16.dp, 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            if (entry.isDirectory) Icons.Default.Folder else Icons.Default.Description,
            contentDescription = null,
            tint = if (entry.isDirectory) LuoColors.accent else LuoColors.textDim,
            modifier = Modifier.size(22.dp)
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(
                entry.name,
                fontFamily = FontFamily.Monospace, fontSize = 14.sp,
                color = LuoColors.textNormal, maxLines = 1
            )
            if (entry.isFile) {
                Text(
                    formatBytes(entry.length()),
                    fontFamily = FontFamily.Monospace, fontSize = 11.sp,
                    color = LuoColors.textFaint
                )
            }
        }
    }
}

private fun formatBytes(bytes: Long): String = when {
    bytes >= 1_073_741_824 -> "%.1f GB".format(bytes / 1_073_741_824.0)
    bytes >= 1_048_576     -> "%.1f MB".format(bytes / 1_048_576.0)
    bytes >= 1_024         -> "%.1f KB".format(bytes / 1_024.0)
    else                   -> "$bytes B"
}
