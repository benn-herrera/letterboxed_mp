set(CMAKE_CXX_STANDARD 20)
set(CMAKE_C_STANDARD 17)

# WTF do we even have to do this? shouldn't this variable just be set?
# https://stackoverflow.com/questions/31661264/how-to-check-if-generator-is-a-multi-config-generator-in-a-cmakelists-txt
get_property(BNG_GENERATOR_IS_MULTI_CONFIG GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)

set(CMAKE_INCLUDE ${PROJECT_SOURCE_DIR}/cmake)

if(BNG_IS_WINDOWS)
  set(BNG_IS_DESKTOP TRUE)
  add_compile_definitions(BNG_IS_WINDOWS)
elseif(BNG_IS_LINUX)
  set(BNG_IS_DESKTOP TRUE)  
  add_compile_definitions(BNG_IS_LINUX)  
elseif(BNG_IS_MACOS)
  set(BNG_IS_DESKTOP TRUE)
  set(BNG_IS_APPLE TRUE)  
  add_compile_definitions(BNG_IS_MACOS BNG_IS_APPLE)
elseif(BNG_IS_IOS)
  set(BNG_IS_MOBILE TRUE)
  set(BNG_IS_APPLE TRUE)
  add_compile_definitions(BNG_IS_IOS BNG_IS_APPLE)
elseif(BNG_IS_ANDROID)
  set(BNG_IS_MOBILE TRUE) 
  add_compile_definitions(BNG_IS_ANDROID) 
elseif(BNG_IS_WASM)
  # https://stunlock.gg/posts/emscripten_with_cmake/#tldr
  set(BNG_PLATFORM_TYPE wasm)
  set(CMAKE_EXECUTABLE_SUFFIX ${BNG_EXE_SUFFIX})
  add_compile_definitions(BNG_IS_WASM)  
  add_compile_options(-Os -sSIDE_MODULE=1 -Werror)
  # emclang does has slightly more stringent warning/error behavior
  # and doesn't like the BNG_IMPL_MOVE implementation in core.h
  # using default move behavior results in a crash, so suppress the warning/error
  add_compile_options(-Wno-nontrivial-memcall)
  add_link_options(-Os -sWASM=1 -sSIDE_MODULE=1 -sSTANDALONE_WASM --no-entry)
else()
  message(FATAL_ERROR "add case for ${BNG_PLATFORM}")
endif()


if(BNG_IS_DESKTOP)
  set(BNG_PLATFORM_TYPE desktop)
  add_compile_definitions(BNG_IS_DESKTOP)
elseif(BNG_IS_MOBILE)
  set(BNG_PLATFORM_TYPE mobile)  
  add_compile_definitions(BNG_IS_MOBILE)
endif()


if(BNG_IS_WINDOWS)
  set(BNG_IS_MSVC TRUE)
else()
  set(BNG_IS_CLANG TRUE)  
endif()

if(BNG_IS_APPLE AND VCPKG_TARGET_TRIPLET MATCHES simulator)
  set(BNG_IS_SIMULATOR TRUE)
endif()


if(BNG_IS_CLANG)
  add_compile_definitions(BNG_IS_CLANG) 
  add_compile_options(-Wall -Werror -fno-exceptions -fno-rtti -fvisibility=hidden)
elseif(BNG_IS_MSVC)
  add_compile_definitions(BNG_IS_MSVC)    
  add_compile_options(/wd4710 /Wall /WX /GR- /EHsc)
else()
  message(FATAL_ERROR "unsupported compiler.")
endif()


add_compile_definitions(
  $<IF:$<CONFIG:Debug>,BNG_DEBUG,>
  $<IF:$<CONFIG:RelWithDebInfo>,${BNG_OPTIMIZED_BUILD_TYPE},>  
)

set(_RELAY_VARS
  BNG_IS_ANDROID
  BNG_IS_APPLE
  BNG_IS_CLANG
  BNG_IS_DESKTOP
  BNG_IS_IOS
  BNG_IS_LINUX
  BNG_IS_MACOS  
  BNG_IS_MOBILE
  BNG_IS_MSVC
  BNG_IS_SIMULATOR
  BNG_IS_WINDOWS
  )

foreach(VAR IN LISTS _RELAY_VARS)
  if(${${VAR}})
    add_compile_definitions(${VAR})
    # message("#define(${VAR}")
  endif()
endforeach()

unset(_RELAY_VARS)


include("${CMAKE_INCLUDE}/options.cmake")


get_filename_component(REPO_ROOT_DIR "${PROJECT_SOURCE_DIR}" DIRECTORY)

set_property(GLOBAL PROPERTY USE_FOLDERS ${BNG_USE_FOLDERS})
# GLOB and GLOB_RECURSE are used for automatic target generation (see lib.cmake)
# add a FORCE_REGEN target for easy regen when files are added/removed/renamed.
add_custom_target(FORCE_REGEN DEPENDS "${CMAKE_BINARY_DIR}/noexist.txt")
set_target_properties(FORCE_REGEN PROPERTIES FOLDER "CMakePredefinedTargets")
add_custom_command(TARGET FORCE_REGEN POST_BUILD
  WORKING_DIRECTORY "${CMAKE_BINARY_DIR}"
  COMMAND "${CMAKE_COMMAND}" "${PROJECT_SOURCE_DIR}")

macro(bng_forbid_in_source_build)
  if("${CMAKE_CURRENT_BINARY_DIR}" STREQUAL "${REPO_ROOT_DIR}" OR "${CMAKE_CURRENT_BINARY_DIR}" STREQUAL "${CMAKE_CURRENT_SOURCE_DIR}")
    message(FATAL_ERROR "In-source building is not supported.")  
  endif()
endmacro()
