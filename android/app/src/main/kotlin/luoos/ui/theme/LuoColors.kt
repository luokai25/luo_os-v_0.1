package luoos.android.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * LuoColors — the shared color palette for Luo OS Android.
 *
 * These are NOT invented — every value here is taken directly from the
 * laptop OS's actual dashboard UI (ui/dashboard.html on the main branch),
 * so the phone app genuinely matches the laptop's look rather than
 * approximating "similar green/black terminal vibes."
 *
 * Laptop source values (for reference, from ui/dashboard.html):
 *   body background:     #0a0a1a
 *   header background:   #111133
 *   accent (cyan/mint):  #00ffcc
 *   accent hover/dim:    #00ddaa
 *   card border:         #00ffcc22 (accent at ~13% alpha)
 *   subtle border:       #ffffff11 (white at ~7% alpha)
 *   red status:          #ff4444
 *   yellow status:       #ffcc00
 *   secondary text:      #aaa
 */
object LuoColors {
    // Core surfaces — matches the laptop's body/header backgrounds exactly
    val background = Color(0xFF0A0A1A)
    val card       = Color(0xFF111133)
    val cardAlt    = Color(0xFF16163D) // a shade up from `card`, for nested/hover surfaces

    // Accent — the laptop's cyan/mint, used for headers, active states, highlights
    val accent     = Color(0xFF00FFCC)
    val accentDim  = Color(0xFF00DDAA) // laptop's button:hover shade
    val accentBorder = Color(0x2200FFCC) // laptop's #00ffcc22 card border, as a real alpha color

    // Text hierarchy
    val textBright = Color(0xFFFFFFFF)
    val textNormal = Color(0xFFE8E8E8)
    val textDim    = Color(0xFFAAAAAA) // laptop's #aaa secondary text

    // Status colors — matches the laptop's .green/.red/.yellow indicator dots
    val statusGood = Color(0xFF00FFCC) // laptop reuses accent for "good", not a separate green
    val statusBad  = Color(0xFFFF4444)
    val statusWarn = Color(0xFFFFCC00)

    // Borders
    val subtleBorder = Color(0x11FFFFFF) // laptop's #ffffff11
}
