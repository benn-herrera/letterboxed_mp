# per https://stunlock.gg/posts/emscripten_with_cmake/#tldr
# build as executable, not library.

set(TARGET bng)

set(GEN_WASM_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_wasm.cpp")
set(GEN_API_JS "${GEN_OUT_DIR}/${GEN_API_NAME}.js")
add_custom_command(
    OUTPUT "${GEN_WASM_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-wasm-binding --api-def="${API_DEF}" --api-h="${GEN_API_H_NAME}" --out-cpp="${GEN_WASM_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    DEPENDS "${GenApiSources_SCRIPT}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)
add_custom_command(
    OUTPUT "${GEN_API_JS}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-js-wrapper --api-def="${API_DEF}" --out-js="${GEN_API_JS}"
    MAIN_DEPENDENCY "${API_DEF}"
    DEPENDS "${GenApiSources_SCRIPT}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)

set(INSTALL_DESTINATION "${BNG_WASM_INSTALL_PATH}")
set(ADDITIONAL_SOURCES "${GEN_WASM_CPP}" "${GEN_API_JS}")

include("${CMAKE_INCLUDE}/target_exe.cmake")

set_source_files_properties(
  "${GEN_WASM_CPP}" "${GEN_API_JS}"
  PROPERTIES
  GENERATED TRUE)

bng_add_link_libraries(core engine)

install(FILES
    "${GEN_API_JS}"
    DESTINATION "${INSTALL_DESTINATION}")
