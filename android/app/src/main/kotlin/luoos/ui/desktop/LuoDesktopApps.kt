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

    // Tier 1, planned but not yet wired to a real screen — still grouped
    // visually with the built apps since they're next in line, but their
    // tier reflects reality (tapping them shows "coming soon" for now).
    LuoDesktopApp("files",     "Files",    Icons.Default.Folder,      "files",     LuoAppTier.CAMERA_TOOLS),
    LuoDesktopApp("terminal",  "Terminal", Icons.Default.Terminal,    "terminal",  LuoAppTier.CAMERA_TOOLS),
    LuoDesktopApp("notes",     "Notes",    Icons.Default.Notes,       "notes",     LuoAppTier.CAMERA_TOOLS),
    LuoDesktopApp("calendar",  "Calendar", Icons.Default.CalendarMonth, "calendar", LuoAppTier.CAMERA_TOOLS),
    LuoDesktopApp("calculator","Calc",     Icons.Default.Calculate,   "calculator",LuoAppTier.CAMERA_TOOLS),

    // Tier 2 — camera-based tools, planned next
    LuoDesktopApp("handtracking", "Hand Track", Icons.Default.PanTool,       "handtracking", LuoAppTier.CAMERA_TOOLS),
    LuoDesktopApp("perception",   "Perception", Icons.Default.RemoveRedEye, "perception",   LuoAppTier.CAMERA_TOOLS),

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
