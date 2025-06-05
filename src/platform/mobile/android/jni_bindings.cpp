#include "bng_api.h"
#include "platform/mobile/mobile.h"
#include "jni_util.h"
#include "core/core.h"

#if 1
using namespace bng::engine;
#define BNG_JNI_METHOD(METHOD) \
    JNIEXPORT JNICALL \
    Java_com_tinybitsinteractive_lbsolverlib_nativecore_NativeCore_##METHOD

extern "C" {
    jlong BNG_JNI_METHOD(createJNI)(JNIEnv *env, jobject thiz) {
        (void)thiz;
       return jlong(EngineInterface::create());
    }

    void BNG_JNI_METHOD(destroyJNI)(JNIEnv *env, jobject thiz, jlong handle) {
        (void)thiz;
        delete (EngineInterface*)handle;
    }

    jstring BNG_JNI_METHOD(setupJNI)(
            JNIEnv *env,
            jobject thiz,
            jlong handle,
            jstring wordsPath,
            jstring cachePath)
    {
        (void)thiz;
        auto jve = JVE(env);
        std::string wordsPathStr = jve.toString(wordsPath);
        std::string cachePathStr = jve.toString(cachePath);
        EngineSetupData setupData{};
        setupData.words_path = wordsPathStr;
        setupData.cache_path = cachePathStr;
        std::string err = ((EngineInterface*)handle)->setup(setupData);
        return jve.toJString(err.c_str());
    }

    jstring BNG_JNI_METHOD(solveJNI)(JNIEnv *env, jobject thiz, jlong handle, jstring box) {
        (void)thiz;
        auto jve = JVE(env);
        std::string boxStr = jve.toString(box);
        BNG_VERIFY(boxStr.size() == 15, "");
        if (boxStr.size() != 15) {
            return jve.toJString("ERROR: invalid puzzle");
        }
        EnginePuzzleData puzzleData{};
        puzzleData.sides[0] = &boxStr[0];
        boxStr[3] = 0;
        puzzleData.sides[1] = &boxStr[4];
        boxStr[7] = 0;
        puzzleData.sides[2] = &boxStr[8];
        boxStr[11] = 0;
        puzzleData.sides[3] = &boxStr[12];

        std::string results = ((EngineInterface*)handle)->solve(puzzleData);
        return jve.toJString(results.c_str());
    }
}
#endif // 0
