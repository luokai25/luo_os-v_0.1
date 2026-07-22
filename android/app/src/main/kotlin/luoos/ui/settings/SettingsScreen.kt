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
import luoos.android.ai.GemmaInference

private val LuoBlack   = Color(0xFF0A0A0A)
private val LuoCard    = Color(0xFF1A1A1A)
private val LuoGreen   = Color(0xFF00FF9F)
private val LuoGreenDim = Color(0xFF00CC7A)
private val LuoGray    = Color(0xFF666666)
private val LuoLightGray = Color(0xFFAAAAAA)
private val LuoWhite   = Color(0xFFE8E8E8)

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    // GemmaInference is cheap to construct — just holds a Context reference
    // and reads file state; it does NOT load the model here.
    val gemma = remember { GemmaInference(context) }
    val modelSizeMb = remember { gemma.modelFile.let { if (it.exists()) it.length() / 1_048_576 else 0 } }

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
                        Text("Gemma 3 1B-IT", color = LuoWhite,
                             fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                        Text("INT4 quantized · CPU · offline",
                             color = LuoGray, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        Spacer(Modifier.height(4.dp))
                        Text(
                            if (modelSizeMb > 0) "✓ Bundled with app (${modelSizeMb} MB)" else "✓ Bundled with app",
                            color = LuoGreen, fontSize = 12.sp, fontFamily = FontFamily.Monospace
                        )
                    }
                    Icon(
                        Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = LuoGreen,
                        modifier = Modifier.size(28.dp)
                    )
                }

                Spacer(Modifier.height(10.dp))

                Text(
                    "No download needed — the model ships inside the app and runs " +
                        "fully offline from first launch.",
                    color = LuoLightGray, fontSize = 12.sp, lineHeight = 17.sp
                )
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
                InfoRow("Min RAM",          "6 GB")
            }
        }

        Spacer(Modifier.height(16.dp))

        // ── About ─────────────────────────────────────────────────────────────
        SectionHeader("ABOUT")
        Surface(color = LuoCard, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {
                InfoRow("Version",  "0.3.0-android")
                InfoRow("AI model", "Gemma 3 1B-IT (Google)")
                InfoRow("Runtime",  "MediaPipe LiteRT")
                InfoRow("Source",   "github.com/luokai25")
            }
        }

        Spacer(Modifier.height(32.dp))
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
