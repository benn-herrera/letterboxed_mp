set(SOURCES_GLOB GLOB) # don't recurse into subdirs
include("${CMAKE_INCLUDE}/target_lib.cmake")

add_dependencies(${TARGET} core api engine)

include("${CMAKE_INCLUDE}/target_reset.cmake")
add_subdirectory(${BNG_PLATFORM})
