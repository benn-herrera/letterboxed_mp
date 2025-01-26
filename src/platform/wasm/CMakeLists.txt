# per https://stunlock.gg/posts/emscripten_with_cmake/#tldr
# build as executable, not library.

set(TARGET bng)

set(BNG_WASM_INSTALL_DIR "${BNG_WASM_INSTALL_DIR}" CACHE PATH "")
if(NOT BNG_WASM_INSTALL_DIR)
    message(FATAL_ERROR "BNG_WASM_INSTALL_DIR must be assigned via -D<VAR>=<VAL> cmake argument")
endif()

set(GEN_WASM_CPP "${GEN_OUT_DIR}/${GEN_API_NAME}_wasm.cpp")

add_custom_command(
    OUTPUT "${GEN_WASM_CPP}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-wasm-binding --api-def="${API_DEF}" --api-h="${GEN_API_H_NAME}" --out-cpp="${GEN_WASM_CPP}"
    MAIN_DEPENDENCY "${API_DEF}"
    DEPENDS "${GenApiSources_SCRIPT}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)

set(ADDITIONAL_SOURCES "${GEN_WASM_CPP}")

include("${CMAKE_INCLUDE}/target_exe.cmake")

set_source_files_properties(
  "${GEN_WASM_CPP}"
  PROPERTIES
  GENERATED TRUE)

bng_add_link_libraries(core api engine)

set_target_properties(${TARGET} PROPERTIES
                      RUNTIME_OUTPUT_DIRECTORY_DEBUG "${BNG_WASM_INSTALL_DIR}"
                      RUNTIME_OUTPUT_DIRECTORY_RELEASE "${BNG_WASM_INSTALL_DIR}"
)
