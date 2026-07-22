# Luo OS — Android

> AI is not an app here. It is the OS.

Luo OS Android turns your phone into an AI-native device. The AI (Gemma 3 1B-IT)
is **bundled inside the app itself** and runs fully offline, locally on your
hardware — no cloud, no subscription, no download step, no internet required
at all after install.

## Download

Get the latest APK from [Releases](../../releases) → `LuoOS-vX.X.X.apk`

**Heads up:** the APK is a large file (~600 MB) because the AI model ships
inside it. That's the tradeoff for zero setup — the whole APK download IS the
model download; there's nothing further to fetch afterward.

**Requirements:**
- Android 12+ (API 31)
- arm64 device (Snapdragon, Dimensity, Exynos — not x86 emulators)
- 6 GB RAM minimum
- ~1.5 GB free storage (model + app data)

**Tested on:** Poco X3 NFC (Snapdragon 732G, 8 GB RAM)

---

## First-run Setup

1. Install the APK (`Settings → Security → Unknown sources`)
2. Open Luo OS — the model extracts itself from the app package into
   internal storage automatically, once, taking a few seconds
3. Go to **Shell** and start talking to Luo — no download screen, no waiting
   on a network connection

---

## Why bundled instead of downloaded

An earlier version of this app downloaded the model at runtime from a URL.
That approach broke in practice — the download button did nothing because the
target URL was a placeholder that was never verified against a real, working
file before shipping.

Bundling the model directly into the APK trades a larger download for zero
runtime failure modes: no broken URLs, no flaky mobile networks mid-download,
no "why is my download stuck" support questions. Android supports APKs up to
roughly 2 GB when sideloaded outside the Play Store, and our model file
(~555 MB) fits comfortably under that with room to spare.

**Why Gemma 3 1B and not a larger model:** every verified, ready-to-use file
for larger Gemma variants on this runtime (MediaPipe's `tasks-genai` /
`.task` format) was either compiled for a specific phone's NPU chip (and
wouldn't run correctly on a Poco X3 NFC's Snapdragon 732G) or gated behind a
Hugging Face account + license click that a CI pipeline can't click through
unattended. Gemma 3 1B has a plain, ungated, CPU-generic `.task` file — the
honest tradeoff is a smaller model in exchange for something that reliably
works out of the box.

**Note on the model source:** the bundled `.task` file comes from a personal
Hugging Face re-upload (`Usern123454321/custom_model.task`), not an official
Google or Google-partner repository. It's the only ready-to-use, ungated file
found for this exact model + runtime combination. This is a known, accepted
tradeoff — that account could remove the file without warning, which would
break future CI builds (existing installed APKs are unaffected either way,
since the model is already bundled inside them).

---

## Architecture

```
android/
├── app/src/main/kotlin/luoos/
│   ├── ai/
│   │   ├── GemmaInference.kt    ← LiteRT wrapper; extracts bundled asset → internal storage, then loads it
│   │   ├── LuoAgent.kt          ← autonomous agent loop + function calling
│   │   ├── LuoTools.kt          ← 12 device tools (files, alarms, apps, memory...)
│   │   └── LuoAiService.kt      ← persistent ForegroundService (model always loaded)
│   ├── ui/
│   │   ├── shell/ShellScreen.kt ← main terminal chat UI
│   │   └── settings/            ← model status display (nothing to download/delete)
│   ├── models/
│   │   └── LuoDatabase.kt       ← Room DB: memory + chat history
│   └── MainActivity.kt
├── app/src/main/assets/models/  ← bundled .task model file lives here (fetched at CI build time, not committed to git)
└── .github/workflows/build-apk.yml  ← fetches model + auto-builds APK on git tag
```

---

## Build from Source

### Prerequisites
- Android Studio Ladybug or newer
- JDK 17
- Android SDK 34
- The model file itself — see below

### Steps

```bash
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1/android

# The model file is NOT committed to git (555 MB — would bloat every clone
# forever). Download it yourself first:
mkdir -p app/src/main/assets/models
curl -fSL -o app/src/main/assets/models/gemma3-1b-it-int4.task \
  "https://huggingface.co/Usern123454321/custom_model.task/resolve/main/gemma3-1b-it-int4.task"

./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

---

## Releasing a New Version

```bash
git tag v0.3.1-android
git push origin v0.3.1-android
```

GitHub Actions automatically:
1. Downloads (or restores from cache) the bundled Gemma 3 1B model
2. Verifies the download is a real, correctly-sized file — hard-fails the
   build rather than shipping a broken model, unlike the old download-based
   version
3. Builds the debug APK with the model baked in as an asset
4. Attaches it to a new GitHub Release

The current workflow builds an **unsigned debug APK** — good enough for
sideloading and testing, but not what you'd submit to the Play Store. Release
signing (keystore-based) is a planned addition, not yet wired up.

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
| First-launch extraction | A few seconds (one-time asset copy) |
| Model load time | Faster than a larger model — 1B class, not 2-4B |
| Inference backend | CPU (LiteRT) |
| NPU | Not used (732G unsupported) |
| RAM usage | Lower than a 2-4B model would need |

---

## Roadmap

- [x] Phase 1 — App shell + UI
- [x] Phase 2 — Local inference (bundled Gemma 3 1B, no download step)
- [x] Phase 3 — Agent tools + function calling
- [ ] Phase 4 — Voice input / camera vision
- [ ] Phase 5 — Memory browser UI
- [ ] Phase 6 — Launcher mode (replace home screen)
- [ ] Release signing for a proper signed APK

---

*Luo OS — built by [@luokai25](https://github.com/luokai25)*
