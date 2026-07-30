package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ai.LuoModelStats
import luoos.android.ui.theme.LuoColors

/**
 * MindCanvasScreen — a live view into what the model is actually doing
 * right now, using LuoModelStats' real, measured numbers rather than a
 * cosmetic animation. This is the honest version of "visualize the AI's
 * mind": actual tokens/sec, actual CPU time, actual thread count.
 */
@Composable
fun MindCanvasScreen() {
    val stats by LuoModelStats.snapshot.collectAsState()

    Column(
        Modifier.fillMaxSize().background(LuoColors.background).padding(20.dp)
    ) {
        Text("Mind Canvas", fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
             fontSize = 20.sp, color = LuoColors.textBright)
        Spacer(Modifier.height(4.dp))
        Text("Live model performance — real, measured values",
             fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim)

        Spacer(Modifier.height(20.dp))

        StatCard("Last generation", "${"%.1f".format(stats.lastTokensPerSecond)} tok/s",
                 "${stats.lastTokenCount} tokens in ${stats.lastElapsedMs}ms")

        StatCard("Rolling average", "${"%.1f".format(stats.rollingAverageTokensPerSecond)} tok/s",
                 "across the last ${stats.totalGenerationCalls.coerceAtMost(20)} calls")

        StatCard("Total generated", "${stats.totalTokensGenerated} tokens",
                 "across ${stats.totalGenerationCalls} generation calls this session")

        StatCard("CPU time", "${stats.cpuTimeMs / 1000.0}s",
                 "accumulated for this app's process (Process.getElapsedCpuTime)")

        StatCard("Threads", "${stats.threadsConfigured}",
                 "configured for llama.cpp inference")

        StatCard("GPU", "not used",
                 "this build disables GPU backends — the device's chip has no usable path for this workload")
    }
}

@Composable
private fun StatCard(label: String, value: String, detail: String) {
    Column(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp)
            .background(LuoColors.card, RoundedCornerShape(10.dp))
            .padding(14.dp)
    ) {
        Text(label, fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim)
        Spacer(Modifier.height(2.dp))
        Text(value, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold,
             fontSize = 20.sp, color = LuoColors.accent)
        Spacer(Modifier.height(2.dp))
        Text(detail, fontFamily = FontFamily.Monospace, fontSize = 11.sp, color = LuoColors.textFaint)
    }
}
