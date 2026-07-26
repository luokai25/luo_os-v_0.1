package luoos.android.ai

import android.os.Process
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update

/**
 * LuoModelStats — real-time resource and performance monitoring for the
 * model, addressing the "control how much CPU or GPU the model is using
 * 24/7, and tokens per sec" request directly.
 *
 * Every number here is a genuine measurement, not an estimate:
 *   - tokensPerSecond / tokenCount come from LlamaInference's
 *     GenerationResult, which is itself built from a real count of decode
 *     iterations in luoos_llama_jni.cpp's nativeGenerate — not guessed from
 *     text length.
 *   - cpuTimeMs comes from Process.getElapsedCpuTime(), Android's official
 *     public API for a process's own accumulated CPU time. This works
 *     without root for OUR OWN process (self-introspection is always
 *     allowed) — the well-known Android 7.0+ restriction on reading other
 *     processes' /proc/[pid]/stat does not apply here.
 *   - threadsConfigured is the real value passed to llama_context_params
 *     (N_THREADS in LlamaInference.kt) — the actual lever that controls how
 *     many CPU cores the model can use during generation. There is
 *     currently no in-app UI to change this at runtime; it's a fixed
 *     constant chosen for the Snapdragon 732G's 2 big + 6 little core
 *     layout. Exposing a live slider for this is a reasonable future
 *     addition once there's a concrete need to trade speed for battery.
 *
 * GPU is honestly reported as not applicable: this build's CMakeLists.txt
 * disables every GPU backend (OpenCL/Vulkan/CUDA) — the Poco X3 NFC's
 * Snapdragon 732G has no usable GPU delegate path for this workload (the
 * same reasoning that led to setPreferredBackend(CPU) when this app still
 * used MediaPipe). Rather than show a fake "0% GPU" stat that implies a GPU
 * path exists and is merely idle, gpuAvailable is a hard `false` so the UI
 * can say plainly "not used on this hardware" instead of implying an unused
 * capability.
 */
object LuoModelStats {

    data class Snapshot(
        val lastTokensPerSecond: Double,
        val lastTokenCount: Int,
        val lastElapsedMs: Long,
        val totalTokensGenerated: Long,
        val totalGenerationCalls: Int,
        val rollingAverageTokensPerSecond: Double,
        val cpuTimeMs: Long,
        val threadsConfigured: Int,
        val gpuAvailable: Boolean
    )

    private const val ROLLING_WINDOW_SIZE = 20

    private val _snapshot = MutableStateFlow(
        Snapshot(
            lastTokensPerSecond = 0.0,
            lastTokenCount = 0,
            lastElapsedMs = 0,
            totalTokensGenerated = 0,
            totalGenerationCalls = 0,
            rollingAverageTokensPerSecond = 0.0,
            cpuTimeMs = 0,
            threadsConfigured = 0,
            gpuAvailable = false
        )
    )

    /** Observe this for a live-updating stats display (e.g. a Settings/Monitor screen). */
    val snapshot: StateFlow<Snapshot> = _snapshot

    // Rolling window of recent tokens/sec measurements, for a stable
    // "how fast is it running right now" figure instead of one noisy sample.
    private val recentRates = ArrayDeque<Double>(ROLLING_WINDOW_SIZE)
    private var totalTokens = 0L
    private var totalCalls = 0

    /** Call this once after a model load succeeds, with the real configured thread count. */
    fun recordThreadsConfigured(threads: Int) {
        _snapshot.update { it.copy(threadsConfigured = threads) }
    }

    /** Call this after every LlamaInference.generate() call, successful or not. */
    fun recordGeneration(result: LlamaInference.GenerationResult) {
        totalTokens += result.tokenCount
        totalCalls += 1

        if (recentRates.size >= ROLLING_WINDOW_SIZE) {
            recentRates.removeFirst()
        }
        if (result.tokensPerSecond > 0) {
            recentRates.addLast(result.tokensPerSecond)
        }

        val rollingAverage = if (recentRates.isEmpty()) 0.0 else recentRates.average()
        val cpuTimeMs = Process.getElapsedCpuTime()

        _snapshot.update {
            it.copy(
                lastTokensPerSecond = result.tokensPerSecond,
                lastTokenCount = result.tokenCount,
                lastElapsedMs = result.elapsedMs,
                totalTokensGenerated = totalTokens,
                totalGenerationCalls = totalCalls,
                rollingAverageTokensPerSecond = rollingAverage,
                cpuTimeMs = cpuTimeMs,
                gpuAvailable = false // see class doc comment — always false on this build
            )
        }
    }

    /** Reset all counters — useful if you want a "since I last checked" view. */
    fun reset() {
        recentRates.clear()
        totalTokens = 0
        totalCalls = 0
        _snapshot.update {
            it.copy(
                lastTokensPerSecond = 0.0,
                lastTokenCount = 0,
                lastElapsedMs = 0,
                totalTokensGenerated = 0,
                totalGenerationCalls = 0,
                rollingAverageTokensPerSecond = 0.0
            )
        }
    }
}
