#pragma once

#include <string>
#include <vector>
#include <jni.h>

struct JVE {
    explicit JVE(JavaVM* _jvm) : env(nullptr), jvm(_jvm) {
        jvm->AttachCurrentThread(&env, nullptr);
    }

    explicit JVE(JNIEnv* _env) : env(_env) {}

    jobject callGetClass(jobject obj, const char*name = nullptr) {
        return callObjectGetter0(obj, name ? name : "getClass", "()Ljava/lang/Class;");
    }

    std::string callGetName(jobject obj) {
        return callStringGetter(obj, "getName");
    }

    jobject callGetIntent(jobject obj, const char*name = nullptr) {
        return callObjectGetter0(obj, name ? name : "getIntent", "()Landroid/content/Intent;");
    }

    std::string callGetStringExtra(jobject obj, const char* key) {
        return callStringByStringGetter(obj, "getStringExtra", key);
    }

    // type signature doc:
    // https://docs.oracle.com/javase/7/docs/technotes/guides/jni/spec/types.html#wp276

    jobject getObjectField(jobject obj, const char* name, const char* type) {
        jclass objC = env->GetObjectClass(obj);
        jfieldID fid = env->GetFieldID(objC, name, type);
        return env->GetObjectField(obj, fid);
    }

    jboolean getBooleanField(jobject obj, const char* name) {
        jclass objC = env->GetObjectClass(obj);
        // Z is type signature for int
        jfieldID fid = env->GetFieldID(objC, name, "Z");
        return env->GetBooleanField(obj, fid);
    }

    int32_t getIntField(jobject obj, const char* name) {
        jclass objC = env->GetObjectClass(obj);
        // I is type signature for int
        jfieldID fid = env->GetFieldID(objC, name, "I");
        return env->GetIntField(obj, fid);
    }

    int64_t getLongField(jobject obj, const char* name) {
        jclass objC = env->GetObjectClass(obj);
        // J is type signature for long
        jfieldID fid = env->GetFieldID(objC, name, "J");
        return env->GetLongField(obj, fid);
    }

    float getFloatField(jobject obj, const char* name) {
        jclass objC = env->GetObjectClass(obj);
        // F is type signature for int
        jfieldID fid = env->GetFieldID(objC, name, "F");
        return env->GetFloatField(obj, fid);
    }

    double getDouble(jobject obj, const char* name) {
        jclass objC = env->GetObjectClass(obj);
        // D is type signature for double
        jfieldID fid = env->GetFieldID(objC, name, "D");
        return env->GetDoubleField(obj, fid);
    }

    std::vector<double> getDoubleArrayField(jobject obj, const char* name) {
        // [D is type signature for array of double
        jobject arrayObj = getObjectField(obj, name, "[D");
        auto& arrayJO = (jdoubleArray&)arrayObj;
        return toVector(arrayJO);
    }

    jobject getAssetManagerField(jobject obj, const char* name) {
        return getObjectField(obj, name, "Landroid/content/res/AssetManager;");
    }

    jobject callObjectGetter0(jobject obj, const char* name, const char* sig) {
        jclass objC = env->GetObjectClass(obj);
        jmethodID mid = env->GetMethodID(objC, name, sig);
        return env->CallObjectMethod(obj, mid);
    }

    jobject callObjectGetter1(jobject obj, const char* name, const char* sig, jobject arg) {
        jclass objC = env->GetObjectClass(obj);
        jmethodID mid = env->GetMethodID(objC, name, sig);
        return env->CallObjectMethod(obj, mid, arg);
    }

    void callOnErrorMethod(jobject obj, const char* msg, bool isFatal) {
        // name and signature must match error handling method in DecorateEngine class in
        // GradleProject/decorate_engine/src/main/kotlin/com/sugarcube/decorate_engine/DecorateEngine.kotlin
        // signature below is equivalent to java:  // void onError(String, Boolean)
        const char* onErrorMethodName = "onError";
        const char* onErrorMethodSig = "(Ljava/lang/String;Z)V";
        jclass clazz = obj ? env->GetObjectClass(obj) : nullptr;
        jmethodID mid = clazz ? env->GetMethodID(clazz, onErrorMethodName, onErrorMethodSig) : nullptr;
        if (mid) {
            env->CallVoidMethod(obj, mid, toJString(msg), (jboolean) isFatal);
            if (env->ExceptionCheck()) {
                env->ExceptionClear();
            }
        }
    }

    std::string toString(jstring jStr) {
        const char* bytes = env->GetStringUTFChars(jStr, nullptr);
        std::string strout(bytes);
        env->ReleaseStringUTFChars(jStr, bytes);
        return strout;
    }

    std::vector<double> toVector(jdoubleArray& arrayJO) {
        auto vecout = std::vector<double>(env->GetArrayLength(arrayJO), 0.0);
        auto arrayData = env->GetDoubleArrayElements(arrayJO, nullptr);
        memcpy(vecout.data(), arrayData, vecout.size() * sizeof(double));
        env->ReleaseDoubleArrayElements(arrayJO, arrayData, 0);
        return vecout;
    }

    jstring toJString(const char* str) {
        return env->NewStringUTF(str ? str : "");
    }

    std::string callStringGetter(jobject obj, const char* name) {
        return toString((jstring) callObjectGetter0(obj, name, "()Ljava/lang/String;"));
    }

    std::string getStringField(jobject obj, const char* name) {
        return toString((jstring)getObjectField(obj, name, "Ljava/lang/String;"));
    }

    std::string callStringByStringGetter(jobject obj, const char* name, const char* key) {
        jstring jkey = env->NewStringUTF(key);
        return toString((jstring) callObjectGetter1(obj, name, "(Ljava/lang/String;)Ljava/lang/String;", jkey));
    }

    JNIEnv* operator->() const { return env; }

private:
    struct Detacher {
        void operator()(JavaVM* p) { if (p) p->DetachCurrentThread(); }
    };
    JNIEnv* env;
    std::unique_ptr<JavaVM, Detacher> jvm;
};
