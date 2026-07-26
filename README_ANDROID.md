# Luo OS — Android

> AI is not an app here. It is the OS.

Luo OS Android turns your phone into an AI-native device, matching the
architecture of the laptop version of Luo OS exactly: **llama.cpp + Qwen2.5**,
bundled inside the app and running fully offline, locally on your hardware —
no cloud, no subscription, no download step, no internet required at all
after install.

## Download

Get the latest APK from [Releases](../../releases) → `LuoOS-vX.X.X.apk`

**Heads up:** the APK is a large file (~1.2 GB) because the AI model ships
inside it. That's the tradeoff for zero setup — the whole APK download IS the
model download; there's nothing further to fetch afterward.

**Requirements:**
- Android 12+ (API 31)
- arm64 device (Snapdragon, Dimensity, Exynos — not x86 emulators)
- 6 GB RAM minimum
- ~2 GB free storage (model + app data)

**Tested on:** Poco X3 NFC (Snapdragon 732G, 8 GB RAM)

---

## First-run Setup

1. Install the APK (`Settings → Security → Unknown sources`)
2. Open Luo OS — the model extracts itself from the app package into
   internal storage automatically, once, taking a few seconds
3. Go to **Shell** and start talking to Luo — no download screen, no waiting
   on a network connection

---

## Why llama.cpp + Qwen2.5, matching the laptop exactly

Two earlier versions of this app used Google's MediaPipe LLM Inference API
with Gemma models. Both were abandoned after real, repeated problems:

- **Gemma 4 E2B**: every genuinely usable file for this runtime was either
  compiled for a specific phone's NPU chip (wouldn't run on a Snapdragon
  732G) or gated behind a Hugging Face license click a CI pipeline can't
  automate unattended.
- **Gemma 3 1B**: found files that loaded, but crashed with a native
  `RET_CHECK` assertion failure inside the model bundle's own structure —
  and this turned out to be a documented, recurring problem across multiple
  independent uploads of this exact model, including inside Google's own
  official sample repository. Not a "bad copy" problem — a fragile format.
- MediaPipe's own Kotlin API additionally changed shape between library
  versions in ways official documentation didn't consistently reflect,
  costing significant time chasing "Unresolved reference" and "Too many
  arguments" compiler errors across version mismatches.

The actual answer was already sitting in this repository: the **laptop
version of Luo OS** (`luokai/core/model_engine.py`) solved this entire
problem already, using **llama.cpp + GGUF model files** instead — a more
mature, battle-tested inference stack with none of these failure modes.
The Android app now matches that architecture directly:

- **Model:** Qwen2.5-1.5B-Instruct, Q4_K_M quantization — the exact model
  the laptop app uses, from the official, ungated `Qwen/Qwen2.5-1.5B-
  Instruct-GGUF` Hugging Face repo (Apache-2.0 licensed, no login required).
- **Runtime:** llama.cpp, compiled fresh from source during every CI build
  (pinned to a specific tag, not a moving branch) via CMake + the Android
  NDK — not a prebuilt third-party library, so every build step is fully
  under this project's control.
- **Verification:** the CI workflow checks both file size AND the exact
  SHA256 hash of the downloaded model against the value confirmed on the
  official Hugging Face file page, before it's ever packaged into an APK.

---

## Architecture

```
android/
├── app/src/main/kotlin/luoos/
│   ├── ai/
│   │   ├── LlamaInference.kt    ← Kotlin/JNI bridge to llama.cpp; extracts bundled asset → internal storage, then loads it
│   │   ├── LuoAgent.kt          ← autonomous agent loop + function calling
│   │   ├── LuoTools.kt          ← 12 device tools (files, alarms, apps, memory...)
│   │   └── LuoAiService.kt      ← persistent ForegroundService (model always loaded)
│   ├── ui/
│   │   ├── theme/LuoColors.kt   ← shared color palette, matched directly to the laptop OS's dashboard UI
│   │   ├── shell/ShellScreen.kt ← main terminal chat UI
│   │   └── settings/            ← model status display (nothing to download/delete)
│   ├── models/
│   │   └── LuoDatabase.kt       ← Room DB: memory + chat history
│   └── MainActivity.kt
├── app/src/main/cpp/
│   ├── CMakeLists.txt           ← fetches llama.cpp source (pinned tag), builds the native library
│   └── luoos_llama_jni.cpp      ← JNI wrapper; every function signature verified against llama.cpp's actual header
├── app/src/main/assets/models/  ← bundled .gguf model file lives here (fetched at CI build time, not committed to git)
└── .github/workflows/build-apk.yml  ← fetches + verifies model, auto-builds APK on git tag
```

---

## Build from Source

### Prerequisites
- Android Studio Ladybug or newer
- JDK 17
- Android SDK 34 + NDK (see `ndkVersion` in `app/build.gradle.kts`)
- CMake (bundled with Android Studio's SDK manager)
- The model file itself — see below

### Steps

```bash
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1/android

# The model file is NOT committed to git (~1.1 GB — would bloat every clone
# forever). Download it yourself first, from the official Qwen repo:
mkdir -p app/src/main/assets/models
curl -fSL -o app/src/main/assets/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"

./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
# First build will take longer than usual — Gradle compiles llama.cpp
# from source via CMake/NDK.
```

---

## Releasing a New Version

```bash
git tag v0.4.1-android
git push origin v0.4.1-android
```

GitHub Actions automatically:
1. Downloads (or restores from cache) the bundled Qwen2.5-1.5B model
2. Verifies the download's size AND exact SHA256 hash — hard-fails the
   build rather than shipping a broken or tampered model
3. Compiles llama.cpp from source (pinned tag) via CMake/NDK, then builds
   the debug APK with the model baked in as an asset
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
| Model | 1.5B parameters, Q4_K_M quantization |
| Inference backend | CPU (llama.cpp, no GPU offload) |
| Threads used | 4 (Snapdragon 732G: 2 big + 6 little cores) |

---

## Roadmap

- [x] Phase 1 — App shell + UI
- [x] Phase 2 — Local inference (bundled model, no download step)
- [x] Phase 3 — Agent tools + function calling
- [x] Phase 4 — Switch to llama.cpp/Qwen2.5, matching the laptop OS exactly
- [ ] Phase 5 — Voice input / camera vision
- [ ] Phase 6 — Memory browser UI
- [ ] Phase 7 — Launcher mode (replace home screen)
- [ ] Release signing for a proper signed APK

---

*Luo OS — built by [@luokai25](https://github.com/luokai25)*
