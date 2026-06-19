package luoos.android.ui.settings

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch
import luoos.android.models.ModelDownloadManager

private val LuoBlack   = Color(0xFF0A0A0A)
private val LuoCard    = Color(0xFF1A1A1A)
private val LuoGreen   = Color(0xFF00FF9F)
private val LuoGreenDim = Color(0xFF00CC7A)
private val LuoGray    = Color(0xFF666666)
private val LuoLightGray = Color(0xFFAAAAAA)
private val LuoWhite   = Color(0xFFE8E8E8)
private val LuoRed     = Color(0xFFFF4444)
private val LuoYellow  = Color(0xFFFFCC00)

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    val scope   = rememberCoroutineScope()
    val downloadManager = remember { ModelDownloadManager(context) }

    var isModelPresent   by remember { mutableStateOf(downloadManager.modelFile.exists()) }
    var downloadState    by remember { mutableStateOf<ModelDownloadManager.DownloadState>(
        ModelDownloadManager.DownloadState.Idle) }
    var showDeleteDialog by remember { mutableStateOf(false) }

    Column(
        Modifier.fillMaxSize().background(LuoBlack)
            .verticalScroll(rememberScrollState()).padding(16.dp)
    ) {
        Text("SETTINGS", fontFamily = FontFamily.Monospace, fontSize = 13.sp,
             color = LuoGray, letterSpacing = 2.sp)
        Spacer(Modifier.height(16.dp))

        // ── Model Section ─────────────────────────────────────────────────────
        SectionHeader("AI MODEL")
        Surface(color = LuoCard, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {

                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Gemma 4 E2B-it", color = LuoWhite,
                             fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                        Text("INT4 quantized · CPU · offline",
                             color = LuoGray, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        Spacer(Modifier.height(4.dp))
                        if (isModelPresent) {
                            val mb = downloadManager.modelFile.length() / 1_048_576
                            Text("✓ Downloaded (${mb} MB)", color = LuoGreen,
                                 fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        } else {
                            Text("⬇ Required — ~1.3 GB", color = LuoYellow,
                                 fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        }
                    }
                    Icon(
                        if (isModelPresent) Icons.Default.CheckCircle else Icons.Default.CloudDownload,
                        contentDescription = null,
                        tint = if (isModelPresent) LuoGreen else LuoYellow,
                        modifier = Modifier.size(28.dp)
                    )
                }

                Spacer(Modifier.height(12.dp))

                // Progress indicator
                when (val s = downloadState) {
                    is ModelDownloadManager.DownloadState.Downloading -> {
                        LinearProgressIndicator(
                            progress = { s.percent / 100f },
                            modifier = Modifier.fillMaxWidth(),
                            color = LuoGreen, trackColor = Color(0xFF2A2A2A)
                        )
                        Spacer(Modifier.height(4.dp))
                        Text("${s.percent}%  —  ${fmtBytes(s.bytesDownloaded)} / ${fmtBytes(s.totalBytes)}",
                             fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = LuoGray)
                    }
                    is ModelDownloadManager.DownloadState.Processing -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(Modifier.size(16.dp), color = LuoGreen, strokeWidth = 2.dp)
                            Spacer(Modifier.width(8.dp))
                            Text("Verifying...", fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoGray)
                        }
                    }
                    is ModelDownloadManager.DownloadState.Error ->
                        Text("⚠ ${s.message}", color = LuoRed,
                             fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                    else -> {}
                }

                Spacer(Modifier.height(8.dp))

                if (!isModelPresent) {
                    val isDownloading = downloadState is ModelDownloadManager.DownloadState.Downloading
                    Button(
                        onClick = {
                            scope.launch {
                                downloadManager.downloadModel().collect { s ->
                                    downloadState = s
                                    if (s is ModelDownloadManager.DownloadState.Complete) isModelPresent = true
                                }
                            }
                        },
                        enabled = !isDownloading,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = LuoGreen, contentColor = LuoBlack)
                    ) {
                        Text("Download Gemma 4 E2B", fontFamily = FontFamily.Monospace, fontSize = 13.sp)
                    }
                } else {
                    OutlinedButton(
                        onClick = { showDeleteDialog = true },
                        colors  = ButtonDefaults.outlinedButtonColors(contentColor = LuoRed),
                        border  = BorderStroke(1.dp, LuoRed)
                    ) {
                        Text("Delete model", fontFamily = FontFamily.Monospace, fontSize = 13.sp)
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // ── Device Info ───────────────────────────────────────────────────────
        SectionHeader("DEVICE")
        Surface(color = LuoCard, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {
                InfoRow("Target device",    "Poco X3 NFC")
                InfoRow("Processor",        "Snapdragon 732G")
                InfoRow("Inference backend","CPU (LiteRT)")
                InfoRow("Speed estimate",   "3–8 tokens/sec")
                InfoRow("Min RAM",          "6 GB")
            }
        }

        Spacer(Modifier.height(16.dp))

        // ── About ─────────────────────────────────────────────────────────────
        SectionHeader("ABOUT")
        Surface(color = LuoCard, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {
                InfoRow("Version",  "0.2.0-android")
                InfoRow("AI model", "Gemma 4 E2B-it (Google)")
                InfoRow("Runtime",  "MediaPipe LiteRT")
                InfoRow("Source",   "github.com/luokai25")
            }
        }

        Spacer(Modifier.height(32.dp))
    }

    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            containerColor   = LuoCard,
            title  = { Text("Delete model?", color = LuoWhite, fontFamily = FontFamily.Monospace) },
            text   = { Text("Removes the model file. You'll need to re-download to use Luo OS.",
                            color = LuoLightGray, fontSize = 14.sp) },
            confirmButton = {
                TextButton(onClick = {
                    downloadManager.deleteModel()
                    isModelPresent = false
                    downloadState  = ModelDownloadManager.DownloadState.Idle
                    showDeleteDialog = false
                }) { Text("Delete", color = LuoRed, fontFamily = FontFamily.Monospace) }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteDialog = false }) {
                    Text("Cancel", color = LuoGray, fontFamily = FontFamily.Monospace)
                }
            }
        )
    }
}

@Composable
private fun SectionHeader(title: String) {
    Text(title, fontFamily = FontFamily.Monospace, fontSize = 11.sp,
         color = LuoGreenDim, letterSpacing = 1.sp)
    Spacer(Modifier.height(6.dp))
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = LuoGray,      fontSize = 13.sp, fontFamily = FontFamily.Monospace)
        Text(value, color = LuoLightGray, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
    }
}

private fun fmtBytes(b: Long) = when {
    b >= 1_073_741_824 -> "%.1f GB".format(b / 1_073_741_824.0)
    b >= 1_048_576     -> "%.1f MB".format(b / 1_048_576.0)
    else               -> "$b B"
}
