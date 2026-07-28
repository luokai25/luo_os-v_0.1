package luoos.android.ui.desktop

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

private fun tierLabel(tier: LuoAppTier): String = when (tier) {
    LuoAppTier.BUILT -> "" // shouldn't be reached — built apps route elsewhere
    LuoAppTier.CAMERA_TOOLS -> "planned next"
    LuoAppTier.AI_VISUALIZATION -> "planned — AI visualization screens"
    LuoAppTier.LARGE_FEATURE -> "planned — larger feature, best-effort build later"
}

@Composable
fun ComingSoonScreen(app: LuoDesktopApp) {
    Box(
        Modifier.fillMaxSize().background(LuoColors.background).padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                app.label,
                fontFamily = FontFamily.Monospace,
                fontSize = 18.sp,
                color = LuoColors.textNormal
            )
            Spacer(Modifier.height(8.dp))
            Text(
                tierLabel(app.tier),
                fontFamily = FontFamily.Monospace,
                fontSize = 12.sp,
                color = LuoColors.textDim,
                textAlign = TextAlign.Center
            )
        }
    }
}
