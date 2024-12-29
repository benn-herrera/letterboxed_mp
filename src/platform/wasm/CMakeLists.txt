set(TARGET bng)
include("${CMAKE_INCLUDE}/target_exe.cmake")

bng_add_link_libraries(core engine)
