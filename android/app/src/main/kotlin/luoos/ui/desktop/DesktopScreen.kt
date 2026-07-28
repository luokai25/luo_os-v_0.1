package luoos.android.ui.desktop

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import luoos.android.ui.theme.LuoColors

/**
 * DesktopScreen — the home screen: a top status strip, then a grid of app
 * icons for every Luo OS app. Tapping an icon opens that app via onOpenApp.
 */
@Composable
fun DesktopScreen(onOpenApp: (LuoDesktopApp) -> Unit) {
    Column(Modifier.fillMaxSize().background(LuoColors.background)) {

        // Top status strip
        Row(
            Modifier.fillMaxWidth().padding(20.dp, 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "LUO OS",
                fontFamily = FontFamily.Monospace,
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = LuoColors.accent
            )
            Spacer(Modifier.weight(1f))
            Text(
                "v0.5",
                fontFamily = FontFamily.Monospace,
                fontSize = 12.sp,
                color = LuoColors.textDim
            )
        }

        // Icon grid
        LazyVerticalGrid(
            columns = GridCells.Fixed(4),
            modifier = Modifier.fillMaxSize().padding(horizontal = 12.dp),
            contentPadding = PaddingValues(bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(luoDesktopApps) { app ->
                DesktopIcon(app = app, onClick = { onOpenApp(app) })
            }
        }
    }
}

@Composable
private fun DesktopIcon(app: LuoDesktopApp, onClick: () -> Unit) {
    Column(
        Modifier
            .clickable(onClick = onClick)
            .padding(4.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            Modifier
                .size(52.dp)
                .background(LuoColors.card, RoundedCornerShape(14.dp)),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                app.icon,
                contentDescription = app.label,
                tint = if (app.tier == LuoAppTier.BUILT) LuoColors.accent else LuoColors.textDim,
                modifier = Modifier.size(26.dp)
            )
        }
        Spacer(Modifier.height(6.dp))
        Text(
            app.label,
            fontFamily = FontFamily.Monospace,
            fontSize = 10.sp,
            color = LuoColors.textNormal,
            maxLines = 1
        )
    }
}
