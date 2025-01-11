
set(TOOL_SCRIPT_DIR "${PROJECT_SOURCE_DIR}/src/tool_scripts")
set(GenApiSources_SCRIPT "${TOOL_SCRIPT_DIR}/gen_api_sources.py")
set(GEN_OUT_DIR "${PROJECT_BINARY_DIR}/generated")

set(API_DIR "${PROJECT_SOURCE_DIR}/src/api")
set(BNG_API_NAME "bng_api")
set(API_DEF "${API_DIR}/${BNG_API_NAME}.json")
set(GEN_API_H_NAME "${BNG_API_H_NAME}.h")

set(GEN_API_H "${GEN_OUT_DIR}/${GEN_API_H_NAME}")
add_custom_command(
    OUTPUT "${GEN_API_H}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-cpp-interface --api-def "${API_DEF}" --out-h "${GEN_API_H}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
set_source_files_properties(
  "${GEN_API_H}"
  PROPERTIES
  GENERATED TRUE)

set(GEN_JNI_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_jni.cpp")
set(GEN_API_KT "${GEN_OUT_DIR}/${GEN_API_NAME}.kt")
add_custom_command(
    OUTPUT "${GEN_JNI_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-jni-binding --api-def "${API_DEF}" --api-h "${GEN_API_H}" --out-cpp "${GEN_JNI_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
add_custom_command(
    OUTPUT "${GEN_API_KT}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-kotlin-wrapper --api-def "${API_DEF}" --out-kt "${GEN_API_KT}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
set_source_files_properties(
  "${GEN_JNI_CPP}" "${GEN_API_KT}"
  PROPERTIES
  GENERATED TRUE)

set(GEN_API_SWIFT_H "${GEN_OUT_DIR}/${GEN_API_NAME}_swift.h")
set(GEN_API_SWIFT_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_swift.cpp")
set(GEN_API_SWIFT "${GEN_OUT_DIR}/${GEN_API_NAME}.swift")
add_custom_command(
    OUTPUT "${GEN_SWIFT_H}" "${GEN_SWIFT_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-swift-binding --api-def "${API_DEF}" --api-h "${GEN_API_H}"
        --out-h "${GEN_SWIFT_H}" --out-cpp "${GEN_SWIFT_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
add_custom_command(
    OUTPUT "${GEN_API_SWIFT}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-swift-wrapper --api-def "${API_DEF}" --swift-h "${GEN_SWIFT_H}"
        --out-swift "${GEN_API_SWIFT}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
set_source_files_properties(
  "${GEN_SWIFT_H}" "${GEN_SWIFT_CPP}" "${GEN_API_SWIFT}"
  PROPERTIES
  GENERATED TRUE)


set(GEN_WASM_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_wasm.cpp")
set(GEN_API_JS "${GEN_OUT_DIR}/${GEN_API_NAME}.js")
add_custom_command(
    OUTPUT "${GEN_WASM_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-wasm-binding --api-def "${API_DEF}" --api-h "${GEN_API_H}" --out-cpp "${GEN_WASM_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
add_custom_command(
    OUTPUT "${GEN_API_JS}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-js-wrapper --api-def "${API_DEF}" --out-js "${GEN_API_JS}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
set_source_files_properties(
  "${GEN_WASM_CPP}" "${GEN_API_JS}"
  PROPERTIES
  GENERATED TRUE)
