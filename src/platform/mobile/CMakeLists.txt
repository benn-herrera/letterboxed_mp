file(GLOB MOBILE_COMMON_SOURCES *.cpp)
file(GLOB MOBILE_COMMON_HEADERS *.h)

include("${CMAKE_INCLUDE}/target_reset.cmake")
add_subdirectory(${BNG_PLATFORM})
