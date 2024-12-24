set(TARGET bng)
include("${CMAKE_INCLUDE}/target_exe.cmake")

add_dependencies(${TARGET} core desktop)
