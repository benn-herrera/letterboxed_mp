set(TARGET bng)
set(LIB_TYPE SHARED)
set(ADDITIONAL_HEADERS ${MOBILE_COMMON_HEADERS})
set(ADDITIONAL_SOURCES ${MOBILE_COMMON_SOURCES})

include("${CMAKE_INCLUDE}/target_lib.cmake")

bng_add_link_libraries(core engine)
