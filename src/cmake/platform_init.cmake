if(CMAKE_SYSTEM_NAME STREQUAL "Android")
  set(BNG_IS_ANDROID TRUE)
  set(BNG_PLATFORM "android")
  set(BNG_EXE_SUFFIX "")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
  set(BNG_IS_MACOS TRUE)
  set(BNG_PLATFORM "macos")
  set(BNG_EXE_SUFFIX "")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Emscripten")
  set(BNG_IS_WASM TRUE)
  set(BNG_PLATFORM "wasm")
  set(BNG_EXE_SUFFIX ".wasm")
elseif(CMAKE_SYSTEM_NAME STREQUAL "iOS")
  set(BNG_IS_IOS TRUE)
  set(BNG_PLATFORM "ios")
  set(BNG_EXE_SUFFIX "")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
  set(BNG_IS_LINUX TRUE)
  set(BNG_PLATFORM "linux")
  set(BNG_EXE_SUFFIX "")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
  set(BNG_IS_WINDOWS TRUE)
  set(BNG_PLATFORM "windows")
  set(BNG_EXE_SUFFIX ".exe")
else()
  message(FATAL_ERROR "Unsupported platform ${CMAKE_SYSTEM_NAME}")
endif()
