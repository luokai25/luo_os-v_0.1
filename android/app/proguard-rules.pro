# llama.cpp JNI bridge — keep the external fun declarations so their names
# still match luoos_llama_jni.cpp's exported JNI symbols if minification is
# ever turned on. (Currently isMinifyEnabled = false for both build types,
# so this isn't active yet, but keeping it accurate for when it is.)
-keepclasseswithmembernames class luoos.android.ai.LlamaInference {
    native <methods>;
}

# Room — keep entity and DAO classes
-keep class luoos.android.models.** { *; }
-keepclassmembers class luoos.android.models.** { *; }

# Kotlin coroutines
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-dontwarn kotlinx.coroutines.**

# Gson — keep serialization classes
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.gson.** { *; }

# Keep Luo AI classes (never obfuscate the agent logic)
-keep class luoos.android.ai.** { *; }

# General Android
-keepattributes SourceFile,LineNumberTable
-keepattributes *Annotation*
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver
