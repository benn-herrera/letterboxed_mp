plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.jetbrains.kotlin.android)
}

android {
    namespace = "com.tinybitsinteractive.lbsolverlib"
    compileSdk = 35

    defaultConfig {
        minSdk = 30

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles("consumer-rules.pro")
        externalNativeBuild {
            cmake {
            }
        }
    }

    buildTypes {
        debug {
            ndk {
                abiFilters.add("arm64-v8a")
            }
            externalNativeBuild {
                cmake {
                    // arguments.add("-DCMAKE_BUILD_TYPE=Debug")
                }
            }
        }
        release {
            ndk {
                abiFilters.add("arm64-v8a")
            }
            externalNativeBuild {
                cmake {
                    // arguments.add("-DCMAKE_BUILD_TYPE=RelWithDebInfo")
                    // arguments.add("-DBNG_OPTIMIZED_BUILD_TYPE=BNG_RELEASE")
                }
            }
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildToolsVersion = "35.0.0"
    externalNativeBuild {
        cmake {
            path = file("../../src/CMakeLists.txt")
            version = "3.31.1"
        }
    }
    ndkVersion = "27.2.12479018"
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}