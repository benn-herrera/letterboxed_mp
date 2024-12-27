set(SOURCES_GLOB GLOB) # don't recurse into subdirs
include("${CMAKE_INCLUDE}/target_lib.cmake")

bng_add_link_libraries(core engine)

include("${CMAKE_INCLUDE}/target_reset.cmake")
add_subdirectory(${BNG_PLATFORM})
