package luoos.android

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.*
import luoos.android.ai.LuoAiService
import luoos.android.ui.shell.ShellScreen
import luoos.android.ui.settings.SettingsScreen

sealed class LuoScreen(val route: String, val label: String, val icon: ImageVector) {
    object Shell    : LuoScreen("shell",    "Shell",    Icons.Default.Code)
    object Agent    : LuoScreen("agent",    "Agent",    Icons.Default.SmartToy)
    object Memory   : LuoScreen("memory",   "Memory",   Icons.Default.Memory)
    object Settings : LuoScreen("settings", "Settings", Icons.Default.Settings)
}

private val screens = listOf(LuoScreen.Shell, LuoScreen.Agent, LuoScreen.Memory, LuoScreen.Settings)

private val LuoBlack   = Color(0xFF0A0A0A)
private val LuoGreen   = Color(0xFF00FF9F)
private val LuoGray    = Color(0xFF444444)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        startForegroundService(LuoAiService.startIntent(this))
        setContent {
            LuoOSTheme { LuoOSRoot() }
        }
    }
}

@Composable
fun LuoOSTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            background    = LuoBlack,
            surface       = Color(0xFF111111),
            primary       = LuoGreen,
            onPrimary     = LuoBlack,
            secondary     = LuoGreen,
            onBackground  = Color(0xFFE8E8E8),
            onSurface     = Color(0xFFE8E8E8)
        ),
        content = content
    )
}

@Composable
fun LuoOSRoot() {
    val navController = rememberNavController()
    Scaffold(
        containerColor = LuoBlack,
        bottomBar = { LuoBottomBar(navController) }
    ) { innerPadding ->
        NavHost(
            navController   = navController,
            startDestination = LuoScreen.Shell.route,
            modifier        = Modifier.padding(innerPadding)
        ) {
            composable(LuoScreen.Shell.route)    { ShellScreen() }
            composable(LuoScreen.Agent.route)    { PlaceholderScreen("Agent Tasks", "Phase 3") }
            composable(LuoScreen.Memory.route)   { PlaceholderScreen("Memory", "Phase 3") }
            composable(LuoScreen.Settings.route) { SettingsScreen() }
        }
    }
}

@Composable
private fun LuoBottomBar(navController: androidx.navigation.NavController) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val current = navBackStackEntry?.destination
    NavigationBar(containerColor = Color(0xFF111111), tonalElevation = 0.dp) {
        screens.forEach { screen ->
            val selected = current?.hierarchy?.any { it.route == screen.route } == true
            NavigationBarItem(
                icon  = { Icon(screen.icon, screen.label, tint = if (selected) LuoGreen else LuoGray) },
                label = { Text(screen.label, fontFamily = FontFamily.Monospace, fontSize = 10.sp,
                               color = if (selected) LuoGreen else LuoGray) },
                selected = selected,
                onClick  = {
                    navController.navigate(screen.route) {
                        popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                        launchSingleTop = true
                        restoreState    = true
                    }
                },
                colors = NavigationBarItemDefaults.colors(indicatorColor = Color(0xFF1E3A2F))
            )
        }
    }
}

@Composable
private fun PlaceholderScreen(name: String, eta: String) {
    Box(Modifier.fillMaxSize().background(LuoBlack), contentAlignment = Alignment.Center) {
        Text("$name\n[coming in $eta]",
            color = Color(0xFF444444),
            fontFamily = FontFamily.Monospace,
            textAlign = TextAlign.Center)
    }
}
