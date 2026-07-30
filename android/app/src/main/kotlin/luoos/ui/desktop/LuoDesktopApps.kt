package luoos.android.ui.desktop

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.ui.graphics.vector.ImageVector

/**
 * LuoDesktopApp — one tile on the desktop's icon grid.
 *
 * The roster and tier grouping below reflect the build order agreed on
 * for this project: apps genuinely built out already (Tier 1), apps
 * planned next (Tier 2 — camera-based tools), then AI-visualization
 * screens (Tier 3), then larger/embedded-style features last (Tier 4).
 * Tiers 2-4 are placeholders for now — tapping them shows a
 * "coming soon" screen rather than crashing or silently doing nothing.
 */
enum class LuoAppTier { BUILT, CAMERA_TOOLS, AI_VISUALIZATION, LARGE_FEATURE }

data class LuoDesktopApp(
    val id: String,
    val label: String,
    val icon: ImageVector,
    val route: String,
    val tier: LuoAppTier
)

val luoDesktopApps: List<LuoDesktopApp> = listOf(
    // Tier 1 — already built and working
    LuoDesktopApp("shell",     "Chat",     Icons.Default.Code,        "shell",     LuoAppTier.BUILT),
    LuoDesktopApp("agent",     "Agent",    Icons.Default.SmartToy,    "agent",     LuoAppTier.BUILT),
    LuoDesktopApp("memory",    "Memory",   Icons.Default.Memory,      "memory",    LuoAppTier.BUILT),
    LuoDesktopApp("settings",  "Settings", Icons.Default.Settings,    "settings",  LuoAppTier.BUILT),
    LuoDesktopApp("files",     "Files",    Icons.Default.Folder,      "files",     LuoAppTier.BUILT),
    LuoDesktopApp("terminal",  "Terminal", Icons.Default.Terminal,    "terminal",  LuoAppTier.BUILT),
    LuoDesktopApp("notes",     "Notes",    Icons.Default.Notes,       "notes",     LuoAppTier.BUILT),
    LuoDesktopApp("calendar",  "Calendar", Icons.Default.CalendarMonth, "calendar", LuoAppTier.BUILT),
    LuoDesktopApp("calculator","Calc",     Icons.Default.Calculate,   "calculator",LuoAppTier.BUILT),

    // Tier 2 — camera-based tools, now built
    LuoDesktopApp("handtracking", "Hand Track", Icons.Default.PanTool,       "handtracking", LuoAppTier.BUILT),
    LuoDesktopApp("perception",   "Perception", Icons.Default.RemoveRedEye, "perception",   LuoAppTier.BUILT),

    // Tier 3 — AI-visualization screens
    LuoDesktopApp("canvas",   "Mind Canvas", Icons.Default.Hub,        "canvas",   LuoAppTier.AI_VISUALIZATION),
    LuoDesktopApp("dreams",   "Dreams",      Icons.Default.NightsStay, "dreams",   LuoAppTier.AI_VISUALIZATION),
    LuoDesktopApp("cells",    "Cells",       Icons.Default.Grain,      "cells",    LuoAppTier.AI_VISUALIZATION),
    LuoDesktopApp("sovereign","Sovereign",   Icons.Default.Shield,     "sovereign",LuoAppTier.AI_VISUALIZATION),

    // Tier 4 — larger, best-effort/simplified features
    LuoDesktopApp("browser",     "Browser",     Icons.Default.Public,     "browser",     LuoAppTier.LARGE_FEATURE),
    LuoDesktopApp("code",        "Code",        Icons.Default.DataObject, "code",        LuoAppTier.LARGE_FEATURE),
    LuoDesktopApp("vscode",      "VS Code",     Icons.Default.IntegrationInstructions, "vscode", LuoAppTier.LARGE_FEATURE),
    LuoDesktopApp("music",       "Music",       Icons.Default.MusicNote, "music",       LuoAppTier.LARGE_FEATURE),
    LuoDesktopApp("blender",     "3D Studio",   Icons.Default.ViewInAr,   "blender",     LuoAppTier.LARGE_FEATURE),
    LuoDesktopApp("worldmonitor","World Monitor", Icons.Default.Public,  "worldmonitor",LuoAppTier.LARGE_FEATURE),
    LuoDesktopApp("multiplayer","Multiplayer", Icons.Default.People,     "multiplayer", LuoAppTier.LARGE_FEATURE)
)
