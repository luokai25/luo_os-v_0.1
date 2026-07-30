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
import luoos.android.ui.apps.CalculatorScreen
import luoos.android.ui.apps.CalendarScreen
import luoos.android.ui.apps.CellsScreen
import luoos.android.ui.apps.DreamsScreen
import luoos.android.ui.apps.FilesScreen
import luoos.android.ui.apps.HandTrackingScreen
import luoos.android.ui.apps.MindCanvasScreen
import luoos.android.ui.apps.NotesScreen
import luoos.android.ui.apps.PerceptionScreen
import luoos.android.ui.apps.SovereignScreen
import luoos.android.ui.apps.TerminalScreen
import luoos.android.ui.boot.BootScreen
import luoos.android.ui.desktop.ComingSoonScreen
import luoos.android.ui.desktop.DesktopScreen
import luoos.android.ui.desktop.LuoAppTier
import luoos.android.ui.desktop.luoDesktopApps
import luoos.android.ui.shell.ShellScreen
import luoos.android.ui.settings.SettingsScreen
import luoos.android.ui.theme.LuoColors

sealed class LuoScreen(val route: String, val label: String, val icon: ImageVector) {
    object Shell    : LuoScreen("shell",    "Shell",    Icons.Default.Code)
    object Agent    : LuoScreen("agent",    "Agent",    Icons.Default.SmartToy)
    object Memory   : LuoScreen("memory",   "Memory",   Icons.Default.Memory)
    object Settings : LuoScreen("settings", "Settings", Icons.Default.Settings)
}

private val screens = listOf(LuoScreen.Shell, LuoScreen.Agent, LuoScreen.Memory, LuoScreen.Settings)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        // NOTE: LuoAiService is started (and bound) from ShellViewModel.bindService(),
        // triggered by ShellScreen's DisposableEffect on ON_START. Starting it again
        // here was redundant and, combined with the service's own state guard, caused
        // a real race: two startForegroundService() calls landing while the service
        // was mid-extraction of the bundled model, launching a second concurrent
        // extraction of the same file and crashing the app shortly after launch.
        setContent {
            LuoOSTheme { LuoOSRoot() }
        }
    }
}

@Composable
fun LuoOSTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            background    = LuoColors.background,
            surface       = LuoColors.card,
            primary       = LuoColors.accent,
            onPrimary     = LuoColors.background,
            secondary     = LuoColors.accent,
            onBackground  = LuoColors.textNormal,
            onSurface     = LuoColors.textNormal
        ),
        content = content
    )
}

@Composable
fun LuoOSRoot() {
    var booted by remember { mutableStateOf(false) }

    if (!booted) {
        BootScreen(onFinished = { booted = true })
        return
    }

    val navController = rememberNavController()
    Scaffold(
        containerColor = LuoColors.background,
        bottomBar = { LuoBottomBar(navController) }
    ) { innerPadding ->
        NavHost(
            navController   = navController,
            startDestination = "desktop",
            modifier        = Modifier.padding(innerPadding)
        ) {
            composable("desktop") {
                DesktopScreen(onOpenApp = { app ->
                    navController.navigate(app.route)
                })
            }
            composable(LuoScreen.Shell.route)    { ShellScreen() }
            composable(LuoScreen.Agent.route)    { PlaceholderScreen("Agent Tasks", "Phase 3") }
            composable(LuoScreen.Memory.route)   { PlaceholderScreen("Memory", "Phase 3") }
            composable(LuoScreen.Settings.route) { SettingsScreen() }
            composable("files")     { FilesScreen() }
            composable("terminal")  { TerminalScreen() }
            composable("notes")     { NotesScreen() }
            composable("calendar")  { CalendarScreen() }
            composable("calculator"){ CalculatorScreen() }
            composable("handtracking") { HandTrackingScreen() }
            composable("perception")   { PerceptionScreen() }
            composable("canvas")    { MindCanvasScreen() }
            composable("dreams")    { DreamsScreen() }
            composable("cells")     { CellsScreen() }
            composable("sovereign") { SovereignScreen() }
            // Every app not yet wired to a real screen falls through to
            // ComingSoonScreen. Routes already registered explicitly above
            // are excluded here to avoid registering the same route twice,
            // which NavHost rejects.
            val alreadyRegisteredRoutes = setOf(
                "shell", "agent", "memory", "settings",
                "files", "terminal", "notes", "calendar", "calculator",
                "handtracking", "perception",
                "canvas", "dreams", "cells", "sovereign"
            )
            luoDesktopApps.filter { it.route !in alreadyRegisteredRoutes }
                .forEach { app ->
                    composable(app.route) { ComingSoonScreen(app) }
                }
        }
    }
}

@Composable
private fun LuoBottomBar(navController: androidx.navigation.NavController) {
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val current = navBackStackEntry?.destination
    NavigationBar(containerColor = LuoColors.card, tonalElevation = 0.dp) {
        screens.forEach { screen ->
            val selected = current?.hierarchy?.any { it.route == screen.route } == true
            NavigationBarItem(
                icon  = { Icon(screen.icon, screen.label, tint = if (selected) LuoColors.accent else LuoColors.textDim) },
                label = { Text(screen.label, fontFamily = FontFamily.Monospace, fontSize = 10.sp,
                               color = if (selected) LuoColors.accent else LuoColors.textDim) },
                selected = selected,
                onClick  = {
                    navController.navigate(screen.route) {
                        popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                        launchSingleTop = true
                        restoreState    = true
                    }
                },
                colors = NavigationBarItemDefaults.colors(indicatorColor = LuoColors.cardAlt)
            )
        }
    }
}

@Composable
private fun PlaceholderScreen(name: String, eta: String) {
    Box(Modifier.fillMaxSize().background(LuoColors.background), contentAlignment = Alignment.Center) {
        Text("$name\n[coming in $eta]",
            color = LuoColors.textDim,
            fontFamily = FontFamily.Monospace,
            textAlign = TextAlign.Center)
    }
}
