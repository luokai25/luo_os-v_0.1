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
import luoos.android.ai.LlamaInference
import luoos.android.ui.theme.LuoColors

@Composable
fun SettingsScreen() {
    val context = LocalContext.current
    // LlamaInference is cheap to construct — just holds a Context reference
    // and reads file state; it does NOT load the model here.
    val llama = remember { LlamaInference(context) }
    val modelSizeMb = remember { llama.modelFile.let { if (it.exists()) it.length() / 1_048_576 else 0 } }

    Column(
        Modifier.fillMaxSize().background(LuoColors.background)
            .verticalScroll(rememberScrollState()).padding(16.dp)
    ) {
        Text("SETTINGS", fontFamily = FontFamily.Monospace, fontSize = 13.sp,
             color = LuoColors.textDim, letterSpacing = 2.sp)
        Spacer(Modifier.height(16.dp))

        // ── Model Section ─────────────────────────────────────────────────────
        SectionHeader("AI MODEL")
        Surface(color = LuoColors.card, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {

                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Qwen2.5-1.5B-Instruct", color = LuoColors.textBright,
                             fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                        Text("Q4_K_M GGUF · llama.cpp · offline",
                             color = LuoColors.textDim, fontSize = 12.sp, fontFamily = FontFamily.Monospace)
                        Spacer(Modifier.height(4.dp))
                        Text(
                            if (modelSizeMb > 0) "✓ Bundled with app (${modelSizeMb} MB)" else "✓ Bundled with app",
                            color = LuoColors.accent, fontSize = 12.sp, fontFamily = FontFamily.Monospace
                        )
                    }
                    Icon(
                        Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = LuoColors.accent,
                        modifier = Modifier.size(28.dp)
                    )
                }

                Spacer(Modifier.height(10.dp))

                Text(
                    "No download needed — the model ships inside the app and runs " +
                        "fully offline from first launch.",
                    color = LuoColors.textNormal, fontSize = 12.sp, lineHeight = 17.sp
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        // ── Device Info ───────────────────────────────────────────────────────
        SectionHeader("DEVICE")
        Surface(color = LuoColors.card, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {
                InfoRow("Target device",    "Poco X3 NFC")
                InfoRow("Processor",        "Snapdragon 732G")
                InfoRow("Inference backend","CPU (llama.cpp)")
                InfoRow("Min RAM",          "6 GB")
            }
        }

        Spacer(Modifier.height(16.dp))

        // ── About ─────────────────────────────────────────────────────────────
        SectionHeader("ABOUT")
        Surface(color = LuoColors.card, shape = RoundedCornerShape(8.dp)) {
            Column(Modifier.padding(16.dp)) {
                InfoRow("Version",  "0.4.0-android")
                InfoRow("AI model", "Qwen2.5-1.5B-Instruct")
                InfoRow("Runtime",  "llama.cpp (matches laptop OS)")
                InfoRow("Source",   "github.com/luokai25")
            }
        }

        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun SectionHeader(title: String) {
    Text(title, fontFamily = FontFamily.Monospace, fontSize = 11.sp,
         color = LuoColors.accentDim, letterSpacing = 1.sp)
    Spacer(Modifier.height(6.dp))
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = LuoColors.textDim,    fontSize = 13.sp, fontFamily = FontFamily.Monospace)
        Text(value, color = LuoColors.textNormal, fontSize = 13.sp, fontFamily = FontFamily.Monospace)
    }
}
