/*
 * JNI example showing the two ways Java finds a native function.
 * Purpose: read it to learn what pattern the original code produces, then go
 * look for that pattern in another app's .so.
 *
 * Build (Android NDK), for example for arm64-v8a:
 *   $NDK/toolchains/llvm/prebuilt/<host>/bin/aarch64-linux-android21-clang \
 *       -shared -o libcheck.so native-lib.c
 * Or create an Android Studio project with a C++ module and put this file in src/main/cpp.
 *
 * Assume the Java side looks like this:
 *   package com.example.app;
 *   public class Native {
 *       static { System.loadLibrary("check"); }
 *       public native boolean checkLicense(String s);   // way 1: conventional name
 *       public native int     secretAdd(int a, int b);  // way 2: dynamic registration
 *   }
 */

#include <jni.h>
#include <string.h>

/* ---- Way 1: conventional naming ----
 * Function name = Java_<package>_<class>_<method>, dots become underscores.
 * Open the .so in Ghidra and filter on "Java_" to see this function at once.
 * Note the two hidden leading parameters: env (x0) and thiz (x1). jstring s is in x2.
 */
JNIEXPORT jboolean JNICALL
Java_com_example_app_Native_checkLicense(JNIEnv *env, jobject thiz, jstring s) {
    const char *in = (*env)->GetStringUTFChars(env, s, 0);  /* pull the string out to process it */
    jboolean ok = (strcmp(in, "JNI-DEMO-2024") == 0) ? JNI_TRUE : JNI_FALSE;
    (*env)->ReleaseStringUTFChars(env, s, in);
    return ok;
}

/* ---- Way 2: dynamic registration ----
 * The real function can have any name (here sub_secret), with NO Java_ prefix.
 * You have to find JNI_OnLoad and read RegisterNatives to learn which method it maps to.
 */
static jint sub_secret(JNIEnv *env, jobject thiz, jint a, jint b) {
    return (a ^ 0x5A) + (b ^ 0x5A);
}

static const JNINativeMethod g_methods[] = {
    /* { Java method name, JNI signature, real function pointer } */
    { "secretAdd", "(II)I", (void *) sub_secret }
};

JNIEXPORT jint JNICALL
JNI_OnLoad(JavaVM *vm, void *reserved) {
    JNIEnv *env = NULL;
    if ((*vm)->GetEnv(vm, (void **) &env, JNI_VERSION_1_6) != JNI_OK)
        return JNI_ERR;

    jclass clazz = (*env)->FindClass(env, "com/example/app/Native");
    if (clazz == NULL)
        return JNI_ERR;

    /* This is the line the reverser has to find in JNI_OnLoad:
       it maps "secretAdd" to sub_secret. */
    (*env)->RegisterNatives(env, clazz, g_methods,
                            sizeof(g_methods) / sizeof(g_methods[0]));
    return JNI_VERSION_1_6;
}
