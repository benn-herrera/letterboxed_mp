set(TARGET bng)
set(LIB_TYPE SHARED)
set(ADDITIONAL_HEADERS ${MOBILE_COMMON_HEADERS} "${GEN_API_KT}")
set(ADDITIONAL_SOURCES ${MOBILE_COMMON_SOURCES} "${GEN_JNI_CPP}")

include("${CMAKE_INCLUDE}/target_lib.cmake")

bng_add_link_libraries(core engine)

# TODO: assign from gradle
set(KOTLIN_BRIDGE_KT_DIR
"${REPO_ROOT_DIR}/kotlin_project/lbsolverlib/src/main/kotlin/com/tinybitsinteractive/lbsolverlib/nativecore")

set(KOTLIN_BRIDGE_KT_DIR "${KOTLIN_BRIDGE_KT_DIR}" CACHE STRING "")

install(FILES
    "${GEN_API_KT}"
    DESTINATION
    "${KOTLIN_BRIDGE_KT_DIR}")
