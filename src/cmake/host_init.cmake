if(PROJECT_BINARY_DIR)
  message(FATAL_ERROR "include in top level CMakeLists.txt before call to project()")
endif()


if(CMAKE_HOST_SYSTEM_NAME STREQUAL "Windows")
  set(BNG_IS_WINDOWS_HOST TRUE)
  set(BNG_HOST "windows")
  set(BNG_HOST_EXE_SUFFIX ".exe")
elseif(CMAKE_HOST_SYSTEM_NAME STREQUAL "Darwin")
  set(BNG_IS_MACOS_HOST TRUE)
  set(BNG_HOST "macos")
  set(BNG_HOST_EXE_SUFFIX "")  
elseif(CMAKE_HOST_SYSTEM_NAME STREQUAL "Linux")
  set(BNG_IS_LINUX_HOST TRUE)
  set(BNG_HOST "linux")
  set(BNG_HOST_EXE_SUFFIX "")
else()
  message(FATAL_ERROR "Unsupported platform ${CMAKE_HOST_SYSTEM_NAME}")
endif()
