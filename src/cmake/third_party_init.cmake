if(NOT PROJECT_SOURCE_DIR)
  message(FATAL_ERROR "include this file after project() call")
endif()
if(NOT (BNG_IS_DESKTOP OR BNG_IS_MOBILE OR BNG_IS_WASM))
  message(FATAL_ERROR "include this file after platform_config.cmake")
endif()

set(THIRD_PARTY_DIR "${PROJECT_SOURCE_DIR}/third_party")
set(THIRD_PARTY_BUILD_DIR "${THIRD_PARTY_DIR}/build/${BNG_PLATFORM}")
set(THIRD_PARTY_INSTALL_DIR "${THIRD_PARTY_DIR}/install/${BNG_PLATFORM}")
set(THIRD_PARTY_INCLUDE_DIR "${THIRD_PARTY_INSTALL_DIR}/include")
set(THIRD_PARTY_LIB_DIR "${THIRD_PARTY_INSTALL_DIR}/lib")
set(THIRD_PARTY_BIN_DIR "${THIRD_PARTY_INSTALL_DIR}/bin")

make_directory("${THIRD_PARTY_BUILD_DIR}")
make_directory("${THIRD_PARTY_INCLUDE_DIR}")
make_directory("${THIRD_PARTY_LIB_DIR}")
make_directory("${THIRD_PARTY_BIN_DIR}")

include_directories("${THIRD_PARTY_DIR}/install/include")

function(bng_add_3p_header_lib NAME REPO VERSION INTERFACE_DIR GLOB)
  set(LIB_SRC_DIR "${THIRD_PARTY_DIR}/${NAME}")
  set(LIB_INCLUDE_DIR "${THIRD_PARTY_INCLUDE_DIR}/${NAME}")
  set(VERSION_VAR "${LIB}_VERSION")

  if (NOT STREQUAL "${${VERSION_VAR}}" "${VERSION}")
    file(REMOVE_RECURSE "${LIB_SRC_DIR}")
    Git("${THIRD_PARTY_DIR}" clone "${REPO}" -c advice.detachedHead=false --depth 1 --branch "${VERSION}" "${NAME}")
    set("${VERSION_VAR}" "${VERSION}" CACHE STRING "" FORCE)
  endif()

  if((NOT INTERFACE_DIR) OR (INTERFACE_DIR STREQUAL "."))
    set(INTERFACE_DIR "${LIB_DIR}")
  else()
    set(INTERFACE_DIR "${LIB_DIR}/${INTERFACE_DIR}")
  endif()

  create_link("${INTERFACE_DIR}" "${LIB_INCLUDE_DIR}")
endfunction()

function(bng_add_3p_lib)
  set(LIB_SRC_DIR "${THIRD_PARTY_DIR}/${NAME}")
  set(LIB_BUILD_DIR "${THIRD_PARTY_BUILD_DIR}/${NAME}")
  set(VERSION_VAR "${LIB}_VERSION")

  if (NOT STREQUAL "${${VERSION_VAR}}" "${VERSION}")
    file(REMOVE_RECURSE "${LIB_SRC_DIR}")
    Git("${THIRD_PARTY_DIR}" clone "${REPO}" -c advice.detachedHead=false --depth 1 --branch "${VERSION}" "${NAME}")
    set(TOOLCHAIN_ARG )
    if (CMAKE_TOOLCHAIN_FILE)
      set(TOOLCHAIN_ARG "-DCMAKE_TOOLCHAIN_FILE=\"${CMAKE_TOOLCHAIN_FILE}\"")
    endif()
    Cmake(
      "${LIB_SRC_DIR}"
      -DCMAKE_SYSTEM_NAME="${CMAKE_SYSTEM_NAME}"
      ${TOOLCHAIN_ARG}
      -G="${CMAKE_GENERATOR}"
      -S="."
      -B="${LIB_BUILD_DIR}"
      -DCMAKE_INSTALL_DIR="${THIRD_PARTY_INSTALL_DIR}"
      # if the API uses std:: types we'll need to deal with the windows debug iterator matching BS
      # for debug windows builds.
      -DCMAKE_BUILD_TYPE=RelWithDebInfo
      # any extra args are used to configure the project e.g. -DBUILD_TESTS=FALSE
       ${ARGN}
    )
    Cmake("${LIB_BUILD_DIR}" --build . --config RelWithDebInfo)
    Cmake("${LIB_BUILD_DIR}" --build . --target install)
    set("${VERSION_VAR}" "${VERSION}" CACHE STRING "" FORCE)
  endif()
endfunction()