// luoos_llama_jni.cpp
//
// JNI bridge between Kotlin (luoos.android.ai.LlamaInference) and llama.cpp's
// C API. Every function call here was checked against the ACTUAL llama.h
// header at the exact pinned tag (b10089) this project builds against —
// not against documentation or examples that might describe a different
// version. This discipline is carried over directly from the lesson learned
// fighting MediaPipe's API drift earlier in this project: the compiler and
// the real header are ground truth, docs and blog posts are not.
//
// Architecture modeled on the real, proven pattern from
// shubham0204/SmolChat-Android's smollm module (llm_inference.cpp), written
// fresh here rather than vendored, so every line is understood.

#include <jni.h>
#include <string>
#include <vector>
#include <android/log.h>

#include "llama.h"

#define TAG "LuoLlamaJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

namespace {

// One inference session's worth of state. A pointer to an instance of this
// struct is handed back to Kotlin as a long (jlong) "handle", the standard
// JNI pattern for holding a native object across multiple JNI calls without
// exposing any C++ types to the Java/Kotlin side.
struct LlamaSession {
    llama_model*   model   = nullptr;
    llama_context* ctx     = nullptr;
    llama_sampler* sampler = nullptr;
    const llama_vocab* vocab = nullptr;

    ~LlamaSession() {
        if (sampler) llama_sampler_free(sampler);
        if (ctx)     llama_free(ctx);
        if (model)   llama_model_free(model);
    }
};

std::string jstringToStdString(JNIEnv* env, jstring jstr) {
    const char* chars = env->GetStringUTFChars(jstr, nullptr);
    std::string result(chars);
    env->ReleaseStringUTFChars(jstr, chars);
    return result;
}

} // namespace

extern "C" {

// ─────────────────────────────────────────────────────────────────────────
// nativeLoadModel — loads a GGUF model from a filesystem path and prepares
// a context + sampler chain for generation. Returns a session handle (0 on
// failure) that Kotlin holds and passes back into every subsequent call.
// ─────────────────────────────────────────────────────────────────────────
JNIEXPORT jlong JNICALL
Java_luoos_android_ai_LlamaInference_nativeLoadModel(
        JNIEnv* env, jobject /* this */,
        jstring modelPath, jint nCtx, jint nThreads,
        jfloat temperature, jint topK, jfloat topP) {

    const std::string path = jstringToStdString(env, modelPath);
    LOGI("Loading model from: %s", path.c_str());

    llama_backend_init();

    // Model loading — verified signature: llama_model_load_from_file(path, params)
    llama_model_params model_params = llama_model_default_params();
    // No GPU offload — Snapdragon 732G has no usable GPU delegate path for
    // this workload (same reasoning as the CPU-only MediaPipe config this
    // replaced).
    model_params.n_gpu_layers = 0;

    llama_model* model = llama_model_load_from_file(path.c_str(), model_params);
    if (!model) {
        LOGE("llama_model_load_from_file failed for path: %s", path.c_str());
        return 0;
    }

    // Context creation — verified signature: llama_init_from_model(model, params).
    // (llama_new_context_with_model is deprecated in this version — confirmed
    // directly from the header, not assumed.)
    llama_context_params ctx_params = llama_context_default_params();
    ctx_params.n_ctx     = static_cast<uint32_t>(nCtx);
    ctx_params.n_batch   = static_cast<uint32_t>(nCtx);
    ctx_params.n_threads = nThreads;
    ctx_params.n_threads_batch = nThreads;

    llama_context* ctx = llama_init_from_model(model, ctx_params);
    if (!ctx) {
        LOGE("llama_init_from_model failed");
        llama_model_free(model);
        return 0;
    }

    // Sampler chain — verified pattern straight from llama.h's own header
    // comment (lines ~1210-1220 of the pinned tag's llama.h): chain_init,
    // then chain_add each sampling stage in order.
    llama_sampler_chain_params sampler_params = llama_sampler_chain_default_params();
    llama_sampler* sampler = llama_sampler_chain_init(sampler_params);
    llama_sampler_chain_add(sampler, llama_sampler_init_top_k(topK));
    llama_sampler_chain_add(sampler, llama_sampler_init_top_p(topP, 1));
    llama_sampler_chain_add(sampler, llama_sampler_init_temp(temperature));
    llama_sampler_chain_add(sampler, llama_sampler_init_dist(LLAMA_DEFAULT_SEED));

    auto* session = new LlamaSession();
    session->model   = model;
    session->ctx     = ctx;
    session->sampler = sampler;
    session->vocab   = llama_model_get_vocab(model);

    LOGI("Model loaded successfully, context size: %d", nCtx);
    return reinterpret_cast<jlong>(session);
}

// ─────────────────────────────────────────────────────────────────────────
// nativeGenerate — tokenizes a prompt, runs the prefill + decode loop, and
// returns the complete generated response as a single string. Streaming is
// handled Kotlin-side by chunking this call per-turn from a coroutine (see
// LlamaInference.kt); a true token-by-token native callback is a possible
// future improvement but isn't required for correctness.
// ─────────────────────────────────────────────────────────────────────────
JNIEXPORT jstring JNICALL
Java_luoos_android_ai_LlamaInference_nativeGenerate(
        JNIEnv* env, jobject /* this */,
        jlong handle, jstring prompt, jint maxTokens) {

    auto* session = reinterpret_cast<LlamaSession*>(handle);
    if (!session || !session->ctx) {
        LOGE("nativeGenerate called with invalid session handle");
        return env->NewStringUTF("");
    }

    const std::string promptStr = jstringToStdString(env, prompt);

    // Tokenize — verified signature:
    // llama_tokenize(vocab, text, text_len, tokens_out, n_tokens_max, add_special, parse_special)
    const int n_prompt_tokens_max = static_cast<int>(promptStr.size()) + 64;
    std::vector<llama_token> promptTokens(n_prompt_tokens_max);

    int n_prompt_tokens = llama_tokenize(
            session->vocab,
            promptStr.c_str(),
            static_cast<int32_t>(promptStr.size()),
            promptTokens.data(),
            n_prompt_tokens_max,
            /* add_special */ true,
            /* parse_special */ true);

    if (n_prompt_tokens < 0) {
        LOGE("Tokenization failed, buffer too small");
        return env->NewStringUTF("");
    }
    promptTokens.resize(n_prompt_tokens);

    std::string response;
    response.reserve(maxTokens * 4); // rough estimate, grows if needed

    // Prefill: process the whole prompt in one batch.
    llama_batch batch = llama_batch_get_one(promptTokens.data(), n_prompt_tokens);

    for (int i = 0; i < maxTokens; i++) {
        int decode_result = llama_decode(session->ctx, batch);
        if (decode_result != 0) {
            LOGE("llama_decode failed with code %d", decode_result);
            break;
        }

        // Sample the next token.
        llama_token newToken = llama_sampler_sample(session->sampler, session->ctx, -1);

        if (llama_vocab_is_eog(session->vocab, newToken)) {
            LOGI("Hit end-of-generation token after %d tokens", i);
            break;
        }

        // Token -> text piece. Verified signature:
        // llama_token_to_piece(vocab, token, buf, length, lstrip, special)
        char pieceBuf[256];
        int pieceLen = llama_token_to_piece(
                session->vocab, newToken, pieceBuf, sizeof(pieceBuf),
                /* lstrip */ 0, /* special */ false);

        if (pieceLen > 0) {
            response.append(pieceBuf, pieceLen);
        }

        // Next batch is just the single new token, continuing the sequence.
        batch = llama_batch_get_one(&newToken, 1);
    }

    return env->NewStringUTF(response.c_str());
}

// ─────────────────────────────────────────────────────────────────────────
// nativeUnload — frees all native resources for a session. Must be called
// exactly once per successful nativeLoadModel call to avoid leaking memory
// (the model + context + sampler chain together can be a significant
// fraction of device RAM).
// ─────────────────────────────────────────────────────────────────────────
JNIEXPORT void JNICALL
Java_luoos_android_ai_LlamaInference_nativeUnload(
        JNIEnv* env, jobject /* this */, jlong handle) {

    auto* session = reinterpret_cast<LlamaSession*>(handle);
    if (session) {
        delete session; // ~LlamaSession() frees sampler/ctx/model in order
        LOGI("Session unloaded");
    }
}

} // extern "C"
