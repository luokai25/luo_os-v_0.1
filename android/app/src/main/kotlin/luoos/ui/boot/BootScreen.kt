package luoos.android.ui.boot

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import luoos.android.ui.theme.LuoColors

/**
 * BootScreen — shown briefly when the app launches, before the desktop.
 * Purely a visual intro; it does not itself wait on the AI model loading
 * (that already happens in the background via LuoAiService once the
 * desktop's Shell app is opened) — this is just the "OS is starting up"
 * moment on screen.
 *
 * @param onFinished called once the intro has run its course, so the
 *                   caller can switch to the desktop.
 */
@Composable
fun BootScreen(onFinished: () -> Unit) {
    var dotCount by remember { mutableStateOf(1) }

    LaunchedEffect(Unit) {
        // Animate a simple "loading..." dot cycle for a moment, then hand off.
        repeat(9) {
            delay(220)
            dotCount = (dotCount % 3) + 1
        }
        onFinished()
    }

    val pulse = rememberInfiniteTransition(label = "pulse")
    val alpha by pulse.animateFloat(
        initialValue = 0.4f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(700), RepeatMode.Reverse),
        label = "alpha"
    )

    Box(
        Modifier.fillMaxSize().background(LuoColors.background),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                "LUO OS",
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                fontSize = 32.sp,
                color = LuoColors.accent
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "starting up" + ".".repeat(dotCount),
                fontFamily = FontFamily.Monospace,
                fontSize = 14.sp,
                color = LuoColors.textDim.copy(alpha = alpha)
            )
        }
    }
}
