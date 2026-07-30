package luoos.android.ui.apps

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors

/**
 * DreamsScreen — meant to visualize background/idle-time processing the AI
 * does when not actively responding to the user. No such system exists yet
 * in this app (LuoAiService currently only runs inference in direct
 * response to a user message), so rather than fabricate fake "dream"
 * content, this screen states that plainly. Building a real idle-time
 * reflection or consolidation pass is a reasonable future addition — see
 * LuoPrompts.SYSTEM_PROMPT_REFLECTION, which is already defined but not
 * yet wired into any automatic trigger.
 */
@Composable
fun DreamsScreen() {
    Box(
        Modifier.fillMaxSize().background(LuoColors.background).padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("Dreams", fontFamily = FontFamily.Monospace, fontSize = 18.sp, color = LuoColors.textBright)
            Spacer(Modifier.height(12.dp))
            Text(
                "No background processing runs yet — the model only\nthinks in direct response to what you ask it.\n\nA real idle-time reflection pass is planned,\nnot fabricated here.",
                fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim,
                textAlign = TextAlign.Center, lineHeight = 18.sp
            )
        }
    }
}
