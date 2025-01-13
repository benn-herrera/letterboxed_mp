#include "api/engine_api.h"
#include "platform/mobile/mobile.h"
#include "jni_util.h"
#include "core/core.h"

#if 0
#define BNG_JNI_METHOD(METHOD) \
    JNIEXPORT JNICALL \
    Java_com_tinybitsinteractive_lbsolverlib_nativecore_NativeCore_##METHOD

extern "C" {
    jlong BNG_JNI_METHOD(createJNI)(JNIEnv *env, jobject thiz) {
        (void)thiz;
       return jlong(bng_engine_create());
    }

    void BNG_JNI_METHOD(destroyJNI)(JNIEnv *env, jobject thiz, jlong handle) {
        (void)thiz;
        bng_engine_destroy((BngEngineHandle)handle);
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
        BngEngineSetupData setupData{};
        setupData.wordsPath = wordsPathStr.c_str();
        setupData.cachePath = cachePathStr.c_str();
        char* err = bng_engine_setup((BngEngineHandle)handle, &setupData);
        auto jerr = jve.toJString(err);
        if (err) {
            free(err);
        }
        return jerr;
    }

    jstring BNG_JNI_METHOD(solveJNI)(JNIEnv *env, jobject thiz, jlong handle, jstring box) {
        (void)thiz;
        auto jve = JVE(env);
        std::string boxStr = jve.toString(box);
        BNG_VERIFY(boxStr.size() == 15, "");
        if (boxStr.size() != 15) {
            return jve.toJString("ERROR: invalid puzzle");
        }
        BngEnginePuzzleData puzzleData{};
        puzzleData.sides[0] = &boxStr[0];
        boxStr[3] = 0;
        puzzleData.sides[1] = &boxStr[4];
        boxStr[7] = 0;
        puzzleData.sides[2] = &boxStr[8];
        boxStr[11] = 0;
        puzzleData.sides[3] = &boxStr[12];

        char* results = bng_engine_solve((BngEngineHandle)handle, &puzzleData);
        auto jresults = jve.toJString(results);
        if (results) {
            free(results);
        }
        return jresults;
    }
}
#endif // 0
