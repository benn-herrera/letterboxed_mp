set(BNG_KOTLIN_WRAPPER_PKG "${BNG_KOTLIN_WRAPPER_PKG}" CACHE STRING "")
set(BNG_KOTLIN_WRAPPER_DIR "${BNG_KOTLIN_WRAPPER_DIR}" CACHE PATH "")

if((NOT BNG_KOTLIN_WRAPPER_PKG) OR (NOT BNG_KOTLIN_WRAPPER_DIR))
    message(
        FATAL_ERROR 
        "BNG_KOTLIN_WRAPPER_PKG and BNG_KOTLIN_WRAPPER_DIR must be defined via -D<VAR>=<VAL> arguments to cmake from build.gradle.kts"
    )
endif()

set(GEN_JNI_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_jni.cpp")
set(GEN_API_KT "${BNG_KOTLIN_WRAPPER_DIR}/${GEN_API_NAME}.kt")

add_custom_command(
    OUTPUT "${GEN_JNI_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-jni-binding --api-def="${API_DEF}" --api-h="${GEN_API_H_NAME}" --api-pkg="${BNG_KOTLIN_WRAPPER_PKG}" --out-cpp="${GEN_JNI_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
add_custom_command(
    OUTPUT "${GEN_API_KT}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-kotlin-wrapper --api-def="${API_DEF}" --out-kt="${GEN_API_KT}"
    MAIN_DEPENDENCY "${API_DEF}"
    DEPENDS "${GenApiSources_SCRIPT}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
set_source_files_properties(
  "${GEN_JNI_CPP}" "${GEN_API_KT}"
  PROPERTIES
  GENERATED TRUE)

set(TARGET bng)
set(LIB_TYPE SHARED)
set(ADDITIONAL_SOURCES ${MOBILE_COMMON_SOURCES} "${GEN_JNI_CPP}" "${GEN_API_KT}")

include("${CMAKE_INCLUDE}/target_lib.cmake")

bng_add_link_libraries(api core engine)
