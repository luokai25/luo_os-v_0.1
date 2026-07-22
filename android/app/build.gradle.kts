plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.ksp)
}

android {
    namespace   = "luoos.android"
    compileSdk  = 34

    defaultConfig {
        applicationId   = "luoos.android"
        minSdk          = 31
        targetSdk       = 34
        versionCode     = 2
        versionName     = "0.3.0-android"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables { useSupportLibrary = true }
        ksp { arg("room.schemaLocation", "$projectDir/schemas") }
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
        jniLibs { pickFirsts += listOf("**/libOpenCL.so", "**/libOpenCL-car-swiftshader.so") }
    }

    // CRITICAL: the bundled Gemma 3 1B model (assets/models/gemma3-1b-it-int4.task,
    // ~555 MB) must NOT be compressed by AAPT2. Compressing it would:
    //   1. Risk OOM/failure during the packageDebug/packageRelease task on a
    //      555 MB binary, and
    //   2. Force the app to fully decompress the asset into a memory buffer at
    //      runtime just to copy it out, instead of a cheap streamed byte copy.
    androidResources {
        noCompress += "task"
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
    implementation(libs.mediapipe.tasks.genai)
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.androidx.datastore.preferences)
    implementation(libs.gson)
    debugImplementation(libs.androidx.ui.tooling)
}
