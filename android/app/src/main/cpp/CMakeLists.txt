cmake_minimum_required(VERSION 3.22.1)
project(luoos_llama)

# ─────────────────────────────────────────────────────────────────────────────
# Fetch llama.cpp source directly during the build — no git submodule, no
# prebuilt third-party AAR to trust blindly. Pinned to a specific tag (not a
# moving branch) so every build is reproducible and won't silently pick up a
# breaking upstream change.
#
# Pinned tag: b10089 (ggml-org/llama.cpp, published 2026-07-22 — current as
# of this writing). Update deliberately, not automatically, if a newer tag
# is ever needed.
# ─────────────────────────────────────────────────────────────────────────────
include(FetchContent)

FetchContent_Declare(
    llama_cpp
    GIT_REPOSITORY https://github.com/ggml-org/llama.cpp.git
    GIT_TAG        b10089
    GIT_SHALLOW    TRUE
)

# Options tuned for a phone build: no GPU backends (Snapdragon 732G has no
# usable GPU delegate path for this workload — confirmed earlier when
# selecting MediaPipe's CPU backend, same reasoning applies here), no
# unnecessary llama.cpp example binaries/tests, no server.
set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_TESTS    OFF CACHE BOOL "" FORCE)
set(LLAMA_BUILD_SERVER   OFF CACHE BOOL "" FORCE)
set(LLAMA_CURL           OFF CACHE BOOL "" FORCE)
set(GGML_OPENCL          OFF CACHE BOOL "" FORCE)
set(GGML_VULKAN          OFF CACHE BOOL "" FORCE)
set(GGML_CUDA            OFF CACHE BOOL "" FORCE)
set(BUILD_SHARED_LIBS    ON  CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(llama_cpp)

# ─────────────────────────────────────────────────────────────────────────────
# Our own minimal JNI wrapper — modeled on the proven, real-world pattern
# from shubham0204/SmolChat-Android's smollm module (llm_inference.cpp +
# JNI binding), written fresh so we understand and control every line
# rather than vendor someone else's C++ verbatim.
# ─────────────────────────────────────────────────────────────────────────────
add_library(luoos_llama SHARED
    luoos_llama_jni.cpp
)

target_link_libraries(luoos_llama
    llama
    log
    android
)

target_include_directories(luoos_llama PRIVATE
    ${llama_cpp_SOURCE_DIR}/include
    ${llama_cpp_SOURCE_DIR}/ggml/include
)
