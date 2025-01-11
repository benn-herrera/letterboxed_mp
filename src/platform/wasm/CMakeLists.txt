# per https://stunlock.gg/posts/emscripten_with_cmake/#tldr
# build as executable, not library.

set(TARGET bng)
set(INSTALL_DESTINATION "${BNG_WASM_INSTALL_PATH}")
set(ADDITIONAL_SOURCES "${BNG_WASM_CPP}" "${BNG_API_JS}")
include("${CMAKE_INCLUDE}/target_exe.cmake")

bng_add_link_libraries(core engine)

install(FILES
    "${GEN_API_JS}"
    DESTINATION "${INSTALL_DESTINATION}")
