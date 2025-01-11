set(ADDITIONAL_HEADERS "${GEN_API_H}")
include("${CMAKE_INCLUDE}/target_lib.cmake")
bng_add_compile_definitions(PRIVATE BNG_ENGINE_IMPL)
bng_add_link_libraries(core)
