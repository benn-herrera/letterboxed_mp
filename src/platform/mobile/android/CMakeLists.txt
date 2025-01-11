set(TARGET bng)
set(LIB_TYPE SHARED)

set(GEN_JNI_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_jni.cpp")
set(GEN_API_KT "${GEN_OUT_DIR}/${GEN_API_NAME}.kt")
add_custom_command(
    OUTPUT "${GEN_JNI_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-jni-binding --api-def="${API_DEF}" --api-h="${GEN_API_H_NAME}" --out-cpp="${GEN_JNI_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
add_custom_command(
    OUTPUT "${GEN_API_KT}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        # TODO: pass package name for generating correct jni binding function names
        # that value should be passed in from gradle via cmake args
        generate-kotlin-wrapper --api-def="${API_DEF}" --out-kt="${GEN_API_KT}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
set_source_files_properties(
  "${GEN_JNI_CPP}" "${GEN_API_KT}"
  PROPERTIES
  GENERATED TRUE)

set(ADDITIONAL_HEADERS ${MOBILE_COMMON_HEADERS} "${GEN_API_KT}")
set(ADDITIONAL_SOURCES ${MOBILE_COMMON_SOURCES} "${GEN_JNI_CPP}")

include("${CMAKE_INCLUDE}/target_lib.cmake")

bng_add_link_libraries(core engine)

# TODO: assign from gradle
set(KOTLIN_BRIDGE_KT_DIR
"${REPO_ROOT_DIR}/kotlin_project/lbsolverlib/src/main/kotlin/com/tinybitsinteractive/lbsolverlib/nativecore")

set(KOTLIN_BRIDGE_KT_DIR "${KOTLIN_BRIDGE_KT_DIR}" CACHE STRING "")

install(FILES
    "${GEN_API_KT}"
    DESTINATION
    "${KOTLIN_BRIDGE_KT_DIR}")
