# per https://stunlock.gg/posts/emscripten_with_cmake/#tldr
# build as executable, not library.

set(TARGET bng)
set(INSTALL_DESTINATION "${BNG_WASM_INSTALL_PATH}")

include("${CMAKE_INCLUDE}/target_exe.cmake")

bng_add_link_libraries(core engine)
