cmake_minimum_required(VERSION 3.30.5 FATAL_ERROR)

#
# pre-init section - before project() call
#

# disallow in-source builds
get_filename_component(REPO_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}" DIRECTORY)
if("${CMAKE_CURRENT_BINARY_DIR}" STREQUAL "${REPO_ROOT_DIR}" OR "${CMAKE_CURRENT_BINARY_DIR}" STREQUAL "${CMAKE_CURRENT_SOURCE_DIR}")
  message(FATAL_ERROR "In-source building is not supported.")  
endif()

# we don't need 5 debug configurations
set(CMAKE_CONFIGURATION_TYPES Debug RelWithDebInfo CACHE STRING "" FORCE)

# Release config always has debug symbols.
if(CMAKE_BUILD_TYPE STREQUAL Release)
  set(CMAKE_BUILD_TYPE RelWithDebInfo CACHE STRING "" FORCE)
endif()

include(cmake/host_init.cmake)

# some platform builds will have defined CMAKE_SYSTEM_NAME
# from the command line as they require setup to occur before project()
if (CMAKE_SYSTEM_NAME)
  include(cmake/platform_init.cmake)
endif()

# set up pre-project values for 3rd party dependency system
# include(cmake/third_party_init.cmake)

#
# project call + project config
#

project(bng VERSION 0.1.0 LANGUAGES CXX C)

if (NOT BNG_PLATFORM)
  include(cmake/platform_init.cmake)
endif()

include(cmake/platform_config.cmake)
# include(cmake/third_party.cmake)
include(cmake/commands.cmake)

include_directories(
  "${PROJECT_SOURCE_DIR}"
)

set(CMAKE_INCLUDE "${PROJECT_SOURCE_DIR}/cmake")

add_subdirectory(api)
add_subdirectory(core)
add_subdirectory(engine)
add_subdirectory(platform)

bng_add_run_all_tests_target()
