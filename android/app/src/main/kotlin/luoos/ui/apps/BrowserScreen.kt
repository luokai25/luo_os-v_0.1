package luoos.android.ui.apps

import android.annotation.SuppressLint
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import luoos.android.ui.theme.LuoColors

/**
 * BrowserScreen — a real, working web browser using Android's built-in
 * WebView. Address bar, back/forward/reload, and a loading indicator, all
 * genuinely functional rather than a static mockup.
 */
@Composable
fun BrowserScreen() {
    var addressBarText by remember { mutableStateOf("https://www.google.com") }
    var currentUrl by remember { mutableStateOf("https://www.google.com") }
    var isLoading by remember { mutableStateOf(false) }
    var webViewRef by remember { mutableStateOf<WebView?>(null) }

    Column(Modifier.fillMaxSize().background(LuoColors.background)) {
        // Address bar + nav controls
        Row(
            Modifier.fillMaxWidth().padding(10.dp, 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = { webViewRef?.goBack() }, modifier = Modifier.size(36.dp)) {
                Icon(Icons.Default.ArrowBack, "Back", tint = LuoColors.accent)
            }
            IconButton(onClick = { webViewRef?.goForward() }, modifier = Modifier.size(36.dp)) {
                Icon(Icons.Default.ArrowForward, "Forward", tint = LuoColors.accent)
            }
            IconButton(onClick = { webViewRef?.reload() }, modifier = Modifier.size(36.dp)) {
                Icon(Icons.Default.Refresh, "Reload", tint = LuoColors.accent)
            }

            TextField(
                value = addressBarText,
                onValueChange = { addressBarText = it },
                modifier = Modifier.weight(1f).padding(start = 4.dp),
                singleLine = true,
                textStyle = TextStyle(fontFamily = FontFamily.Monospace, fontSize = 13.sp, color = LuoColors.textNormal),
                colors = TextFieldDefaults.colors(
                    focusedContainerColor = LuoColors.cardAlt,
                    unfocusedContainerColor = LuoColors.cardAlt,
                    focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                    cursorColor = LuoColors.accent
                ),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Go),
                keyboardActions = KeyboardActions(onGo = {
                    currentUrl = normalizeUrl(addressBarText)
                    webViewRef?.loadUrl(currentUrl)
                })
            )
        }

        if (isLoading) {
            LinearProgressIndicator(
                modifier = Modifier.fillMaxWidth(),
                color = LuoColors.accent,
                trackColor = LuoColors.cardAlt
            )
        }

        AndroidWebView(
            url = currentUrl,
            onWebViewReady = { webViewRef = it },
            onLoadingChanged = { isLoading = it },
            onUrlChanged = { newUrl -> addressBarText = newUrl }
        )
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun AndroidWebView(
    url: String,
    onWebViewReady: (WebView) -> Unit,
    onLoadingChanged: (Boolean) -> Unit,
    onUrlChanged: (String) -> Unit
) {
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
                webViewClient = object : WebViewClient() {
                    override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                        onLoadingChanged(true)
                        url?.let(onUrlChanged)
                    }
                    override fun onPageFinished(view: WebView?, finishedUrl: String?) {
                        onLoadingChanged(false)
                        finishedUrl?.let(onUrlChanged)
                    }
                }
                loadUrl(url)
                onWebViewReady(this)
            }
        }
    )
}

private fun normalizeUrl(input: String): String {
    val trimmed = input.trim()
    return when {
        trimmed.startsWith("http://") || trimmed.startsWith("https://") -> trimmed
        trimmed.contains(" ") || !trimmed.contains(".") ->
            "https://www.google.com/search?q=${android.net.Uri.encode(trimmed)}"
        else -> "https://$trimmed"
    }
}
