plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.ksp)
}

android {
    namespace   = "luoos.android"
    compileSdk  = 34
    ndkVersion  = "26.3.11579264"

    defaultConfig {
        applicationId   = "luoos.android"
        minSdk          = 31
        targetSdk       = 34
        versionCode     = 3
        versionName     = "0.4.0-android"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables { useSupportLibrary = true }
        ksp { arg("room.schemaLocation", "$projectDir/schemas") }

        ndk {
            // Snapdragon 732G (Poco X3 NFC) is arm64 only — matches the
            // laptop OS's own approach of targeting one architecture cleanly
            // rather than shipping every ABI.
            abiFilters += "arm64-v8a"
        }

        externalNativeBuild {
            cmake {
                // Match the laptop OS's actual inference engine: llama.cpp,
                // compiled fresh in CI rather than trusting a prebuilt
                // third-party AAR. See app/src/main/cpp/CMakeLists.txt.
                //
                // Deliberately NOT setting -march: the official llama.cpp
                // Android docs' example uses -march=armv8.7a, but the
                // Poco X3 NFC's Snapdragon 732G is confirmed ARMv8.2-A
                // (Cortex-A76 + A55) — an older instruction set. Using the
                // docs' flag verbatim would compile a binary that crashes
                // with an illegal-instruction fault the first time it hit an
                // unsupported opcode. Leaving -march unset lets the NDK
                // toolchain use its safe default baseline for
                // ANDROID_PLATFORM, which is always guaranteed compatible.
                arguments += listOf(
                    "-DANDROID_STL=c++_shared",
                    "-DANDROID_PLATFORM=android-31",
                    "-DGGML_OPENMP=OFF",
                    "-DGGML_LLAMAFILE=OFF"
                )
                cppFlags += "-std=c++17"
            }
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
        debug { isDebuggable = true }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions { jvmTarget = "17" }

    buildFeatures {
        compose     = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.8"
    }

    packaging {
        resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" }
    }

    // CRITICAL: the bundled Qwen2.5-1.5B-Instruct GGUF model (~1 GB, Q4_K_M
    // quantization) must NOT be compressed by AAPT2. Compressing it would:
    //   1. Risk OOM/failure during the packageDebug/packageRelease task on a
    //      large binary, and
    //   2. Force the app to fully decompress the asset into a memory buffer at
    //      runtime just to copy it out, instead of a cheap streamed byte copy.
    androidResources {
        noCompress += "gguf"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.material.icons.extended)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.androidx.datastore.preferences)
    implementation(libs.gson)
    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.view)
    implementation(libs.mlkit.pose.detection)
    implementation(libs.mlkit.face.mesh.detection)
    debugImplementation(libs.androidx.ui.tooling)
}
