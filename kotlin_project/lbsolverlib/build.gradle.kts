plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.jetbrains.kotlin.android)
}

android {
    namespace = "com.tinybitsinteractive.lbsolverlib"
    compileSdk = 36

    defaultConfig {
        minSdk = 30

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        consumerProguardFiles("consumer-rules.pro")
        externalNativeBuild {
            val project_dir = project.buildFile.parent
            val pkg_name = "${namespace}.nativecore"
            val pkg_dir = pkg_name.replace(".", "/")
            val gen_kt_dir = "${project_dir}/src/main/kotlin/${pkg_dir}"
            cmake {
                arguments.add("-DBNG_KOTLIN_WRAPPER_PKG=${pkg_name}")
                arguments.add("-DBNG_KOTLIN_WRAPPER_DIR=${gen_kt_dir}")
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
            version = "3.31.6"
        }
    }
    ndkVersion = "28.1.13356709"
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
}