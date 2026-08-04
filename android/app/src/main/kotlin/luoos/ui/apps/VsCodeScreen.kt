package luoos.android.ui.apps

import android.annotation.SuppressLint
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import luoos.android.ui.theme.LuoColors

/**
 * VsCodeScreen — genuinely the real VS Code, not an approximation: this
 * loads vscode.dev, Microsoft's own official web build of VS Code, inside
 * a WebView. This is the same underlying technique GitHub uses for its own
 * browser-based editor — running the actual editor in a browser context
 * rather than trying to port the full desktop app to Android.
 *
 * Reuses the same WebView + progress-indicator pattern as BrowserScreen.kt.
 */
@Composable
fun VsCodeScreen() {
    var isLoading by remember { mutableStateOf(true) }

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        if (isLoading) {
            LinearProgressIndicator(
                modifier = Modifier.fillMaxWidth(),
                color = LuoColors.accent,
                trackColor = LuoColors.cardAlt
            )
        }
        VsCodeWebView(onLoadingChanged = { isLoading = it })
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun VsCodeWebView(onLoadingChanged: (Boolean) -> Unit) {
    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                // vscode.dev is a full single-page web app — it needs a
                // realistic desktop-class user agent or it can serve a
                // reduced mobile experience; this keeps it running as the
                // genuine full editor.
                settings.userAgentString = settings.userAgentString
                    .replace("Mobile", "").replace("Android", "X11; Linux x86_64")

                webViewClient = object : WebViewClient() {
                    override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                        onLoadingChanged(true)
                    }
                    override fun onPageFinished(view: WebView?, url: String?) {
                        onLoadingChanged(false)
                    }
                }
                loadUrl("https://vscode.dev")
            }
        }
    )
}
