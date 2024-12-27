#include "core/core.h"
#include "jni_util.h"
#define BNG_JNI_METHOD(METHOD) \
    JNIEXPORT JNICALL \
    Java_com_tinybitsinteractive_lbsolverlib_nativecore_NativeCore_##METHOD

extern "C" {
    jstring BNG_JNI_METHOD(setupJNI)(JNIEnv *env, jobject thiz, jstring words_path) {
            (void) thiz;
            (void) words_path;
            return JVE(env).toJString("NYI");
    }

    jstring BNG_JNI_METHOD(solveJNI)(JNIEnv *env, jobject thiz, jstring box) {
        (void) thiz;
        (void) box;
        return JVE(env).toJString("NYI");
    }
}