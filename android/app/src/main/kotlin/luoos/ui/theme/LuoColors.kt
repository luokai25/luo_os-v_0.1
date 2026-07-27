package luoos.android.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * LuoColors — the shared color palette for Luo OS Android.
 *
 * Switched to match index.html (the real, complete desktop OS — a full
 * window-manager interface with ~20 apps) rather than the smaller
 * ui/dashboard.html this file matched before. index.html is the actual,
 * primary Luo OS interface; dashboard.html appears to be a lighter
 * companion page with its own, different palette.
 *
 * Every value below was read directly from index.html's dark-theme :root
 * block and its per-component styles (window controls, chat bubbles,
 * terminal), not invented or approximated:
 *   base background:      #0d0d0d
 *   card/panel background:#141414
 *   input background:     #1a1a1a
 *   border:               #2a2a2a
 *   text (primary):       #e8e8e8
 *   text (secondary):     #999999
 *   text (tertiary):      #555555
 *   accent (sky blue):    #4fc3f7
 *   accent2 (violet):     #7c4dff
 *   window control red:   #ff5f57 (macOS-style traffic-light close button)
 *   window control amber: #febc2e (minimize button)
 *   window control green: #28c840 (maximize button)
 *   AI chat avatar tint:  rgba(0,200,255,.12) — a slightly different blue
 *                         than --accent, used specifically for the AI's
 *                         avatar background in chat
 *   user chat avatar/bubble tint: rgba(124,58,237,.12 / .15) — violet,
 *                         matching --accent2
 *   terminal background:  #010a04 (near-black, greenish)
 *   terminal text:        #00ff9d (bright green — deliberately different
 *                         from the rest of the OS's blue/violet palette,
 *                         since the laptop's terminal window is styled
 *                         as its own distinct "old-school console" look)
 */
object LuoColors {
    // Core surfaces
    val background = Color(0xFF0D0D0D)
    val card       = Color(0xFF141414)
    val cardAlt    = Color(0xFF1A1A1A) // matches --bg-input, for input fields and nested surfaces

    // Accents — the OS uses TWO accents, not one: sky blue for primary/AI
    // context, violet for user/secondary context. Using only one accent
    // everywhere (as the previous palette did) loses this real distinction.
    val accent      = Color(0xFF4FC3F7) // --accent: sky blue — primary actions, AI context
    val accent2     = Color(0xFF7C4DFF) // --accent2: violet — user context, secondary actions
    val accentDim   = accent.copy(alpha = 0.66f)
    val accentBorder = accent.copy(alpha = 0.13f)

    // Text hierarchy
    val textBright = Color(0xFFFFFFFF)
    val textNormal = Color(0xFFE8E8E8) // --text
    val textDim    = Color(0xFF999999) // --text2
    val textFaint  = Color(0xFF555555) // --text3

    // Window chrome — genuine macOS-style traffic lights, not a custom scheme
    val windowClose    = Color(0xFFFF5F57)
    val windowMinimize = Color(0xFFFEBC2E)
    val windowMaximize = Color(0xFF28C840)

    // Chat — two distinct tints, matching the real per-role styling
    val aiAvatarBg     = Color(0xFF00C8FF).copy(alpha = 0.12f)
    val userAvatarBg   = accent2.copy(alpha = 0.12f)
    val userBubbleBg   = accent2.copy(alpha = 0.15f)
    val userBubbleBorder = accent2.copy(alpha = 0.20f)

    // Terminal — deliberately its own look, not derived from the main accent
    val terminalBackground = Color(0xFF010A04)
    val terminalText       = Color(0xFF00FF9D)

    // Status colors
    val statusGood = Color(0xFF00CC66)
    val statusBad  = Color(0xFFFF4D6D)
    val statusWarn = Color(0xFFFFAA00)

    // Borders
    val subtleBorder = Color(0xFF2A2A2A) // --border
}
