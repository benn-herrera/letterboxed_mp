# adds a library target and sets up test targets for source files under tests/
# target name comes from current directory name by default
# may be overridden by setting TARGET before including this file

# controls whether target_common generates a unity build AIO
if(NOT DEFINED AUTO_AIO)
  set(AUTO_AIO TRUE)
endif()

# defines TARGET from name of current directory
# define HEADERS, SOURCES, AIO_SOURCE
include("${CMAKE_INCLUDE}/target_common.cmake")

if (NOT LIB_TYPE)
  if (NOT SOURCES)
    set(LIB_TYPE INTERFACE)
  else()
    set(LIB_TYPE STATIC)
  endif()
endif()

add_library(
  ${TARGET} ${LIB_TYPE}
  ${HEADERS} 
  ${SOURCES}
  ${AIO_SOURCE}
  )

if(INSTALL_DESTINATION)
  install(TARGETS ${TARGET} DESTINATION "${INSTALL_DESTINATION}")
endif()

bng_add_lib_test_targets()
