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
 * SovereignScreen — meant to represent the AI acting autonomously, without
 * a user directly prompting each step (e.g. running scheduled tasks or
 * making decisions on its own). No such system exists yet: every action
 * this app's agent takes (see LuoAgent.kt) happens strictly in response to
 * a user message, in a single foreground request/response cycle. Rather
 * than fabricate a fake "autonomy" toggle or status here, this screen
 * states that plainly. A real scheduled/background agent — and the
 * permission model it would need — is a real, separate design task, not
 * something to fake a UI for ahead of building it.
 */
@Composable
fun SovereignScreen() {
    Box(
        Modifier.fillMaxSize().background(LuoColors.background).padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("Sovereign", fontFamily = FontFamily.Monospace, fontSize = 18.sp, color = LuoColors.textBright)
            Spacer(Modifier.height(12.dp))
            Text(
                "Luo currently only acts when you ask it something —\nthere's no autonomous mode running in the background.\n\nBuilding real scheduled/independent actions, and the\npermissions they'd need, is a real next step, not\nsomething to fake here ahead of time.",
                fontFamily = FontFamily.Monospace, fontSize = 12.sp, color = LuoColors.textDim,
                textAlign = TextAlign.Center, lineHeight = 18.sp
            )
        }
    }
}
