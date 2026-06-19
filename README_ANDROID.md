# Luo OS — Android

> AI is not an app here. It is the OS.

Luo OS Android turns your phone into an AI-native device. The AI (Gemma 4 E2B-it) runs fully offline, locally on your hardware — no cloud, no subscription, no internet required after setup.

## Download

Get the latest APK from [Releases](../../releases) → `LuoOS-vX.X.X.apk`

**Requirements:**
- Android 12+ (API 31)
- arm64 device (Snapdragon, Dimensity, Exynos — not x86 emulators)
- 6 GB RAM minimum
- ~2 GB free storage (for the model)

**Tested on:** Poco X3 NFC (Snapdragon 732G, 8 GB RAM)

---

## First-run Setup

1. Install the APK (`Settings → Security → Unknown sources`)
2. Open Luo OS → tap **Settings**
3. Tap **Download** next to Gemma 4 E2B (~1.3 GB) — use WiFi
4. Wait for the model to load (~15–20 seconds)
5. Go back to **Shell** and start talking to Luo

---

## Architecture

```
android/
├── app/src/main/kotlin/luoos/
│   ├── ai/
│   │   ├── GemmaInference.kt    ← LiteRT wrapper for Gemma 4 E2B
│   │   ├── LuoAgent.kt          ← autonomous agent loop + function calling
│   │   ├── LuoTools.kt          ← 12 device tools (files, alarms, apps, memory...)
│   │   └── LuoAiService.kt      ← persistent ForegroundService (model always loaded)
│   ├── ui/
│   │   ├── shell/ShellScreen.kt ← main terminal chat UI
│   │   └── settings/            ← model download + config
│   ├── models/
│   │   ├── LuoDatabase.kt       ← Room DB: memory + chat history
│   │   └── ModelDownloadManager.kt
│   └── MainActivity.kt
└── .github/workflows/build-apk.yml  ← auto-builds APK on git tag
```

---

## Build from Source

### Prerequisites
- Android Studio Ladybug or newer
- JDK 17
- Android SDK 34

### Steps

```bash
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1/android
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

### Release build (requires keystore)

```bash
./gradlew assembleRelease
```

---

## Releasing a New Version

```bash
git tag v0.2.1-android
git push origin v0.2.1-android
```

GitHub Actions automatically:
1. Builds the release APK
2. Signs it with your keystore (set `KEYSTORE_BASE64`, `KEY_ALIAS`, `KEY_PASSWORD`, `STORE_PASSWORD` in repo Secrets)
3. Attaches it to a new GitHub Release

---

## Tools Available to Luo Agent

| Tool | What it does |
|---|---|
| `list_files` | Browse device storage |
| `read_file_text` | Read text files |
| `open_app` | Launch any installed app |
| `set_alarm` | Set device alarms |
| `send_notification` | Push notifications |
| `remember` | Save to permanent memory |
| `recall` | Search memory |
| `get_time` | Current date/time |
| `web_search` | Open web search (needs internet) |
| `open_url` | Open URLs in browser |
| `list_installed_apps` | List all launchable apps |
| `get_storage_info` | Disk usage |

---

## Performance on Poco X3 NFC

| Metric | Value |
|---|---|
| Model load time | ~15–20 seconds |
| Tokens/sec (chat) | 3–8 tok/s |
| RAM usage | ~2.3 GB for model |
| Inference backend | CPU (LiteRT) |
| NPU | Not used (732G unsupported) |

---

## Roadmap

- [x] Phase 1 — App shell + UI
- [x] Phase 2 — Gemma 4 E2B local inference
- [x] Phase 3 — Agent tools + function calling
- [ ] Phase 4 — Voice input / camera vision
- [ ] Phase 5 — Memory browser UI
- [ ] Phase 6 — Launcher mode (replace home screen)

---

*Luo OS — built by [@luokai25](https://github.com/luokai25)*
