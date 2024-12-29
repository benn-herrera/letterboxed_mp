#!/usr/bin/env bash
THIS_SCRIPT=$(basename "${0}")
THIS_DIR=$(dirname "${0}")
# can't rely on realpath existing
THIS_DIR=$(cd "${THIS_DIR}"; pwd)

function is_true() {
  case "${1}" in
    # ${1^^} syntax for upper casing not available in old mac bash    
    t*|T*|y*|Y*|1) return 0;;
  esac
  return 1
}

function is_in() {
  local sub=${1}
  local str=${2}
  [[ "${str/${sub}/}" != "${str}" ]]
}

function usage_and_die() {
  cat << __EOF
usage: ${THIS_SCRIPT} [--help] | [--clean] [--ios|--ios-release|--no-ios] [--ios-sim|--no-ios] [cmake_arg1]...
    note: bootstrap.sh must have been run first.
    --ios: build debug for ios device
    --ios-release: build release for ios device
    --no-ios: no ios device build
    --ios-sim: build debug for ios simulator
    --no-ios-sim: no ios simulator build   
    --clean: delete build directory first
    any cmake args must come after --clean, --build.
    src/cmake/options.cmake:
    $(awk '{ print (NR == 1 ? "" : "    ") $0 }' "${THIS_DIR}/src/cmake/options.cmake")
__EOF
  exit ${1:-0}
}


# respect envars
GEN_CLEAN=${GEN_CLEAN:-false}
BUILD_IOS=${BUILD_IOS:-}
BUILD_IOS_SIM=${BUILD_IOS_SIM:-Debug}
#CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Ninja Multi-Config"}
CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Xcode"}

if [[ "${BUILD_IOS}" == "None" ]]; then
  BUILD_IOS=
fi
if [[ "${BUILD_IOS_SIM}" == "None" ]]; then
  BUILD_IOS_SIM=
fi

VCPKG_DIR=src/vcpkg
export VCPKG_ROOT=${THIS_DIR}/${VCPKG_DIR}
export PATH=${VCPKG_ROOT}:${PATH}

VCPKG=${VCPKG_ROOT}/vcpkg

case "$(uname)" in
  Darwin*) IS_MAC=true;;
  *) echo "unsupported platform $(uname). swift project can only be built on macOS." 1>&2; exit 1;;
esac

while [[ -n "${1}" ]]; do
  case "${1}" in
    -h*|--h*|-u*|--u*) usage_and_die;;
    --clean|-c) GEN_CLEAN=true; shift;;
    --no-ios) BUILD_IOS=; shift;;
    --no-ios-sim*) BUILD_IOS_SIM=; shift;;
    --ios) BUILD_IOS=Debug; shift;;
    --ios-rel*) BUILD_IOS=RelWithDebInfo; shift;;
    --ios-sim) BUILD_IOS_SIM=Debug; shift;;
    *) break;;
  esac
done

cd "${THIS_DIR}"

if ! [[ -f .venv/.activate && -x "${VCPKG}" ]]; then
  echo "run bootstrap.sh first." 2>&1
  exit 1
fi

function run_cmake_gen() {
  if ${GEN_CLEAN}; then
    (/bin/rm -rf "${BUILD_DIR}" 2>&1) > /dev/null
  fi

  if [[ -f "${BUILD_DIR}/CMakeCache.txt" ]]; then
    if ! (set -x && cd "${BUILD_DIR}" && cmake . "${@}"); then
      return 1
    fi
    return 0
  fi

  if [[ -n "${CMAKE_BUILD_TYPE:-}" ]]; then
    set -- "-DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}" "${@}"
  fi
  if [[ -n "${VCPKG_TARGET_TRIPLET:-}" ]]; then
    set -- "-DVCPKG_TARGET_TRIPLET=${VCPKG_TARGET_TRIPLET}" "${@}"
  fi
  if [[ -n "${BNG_OPTIMIZED_BUILD_TYPE:-}" ]]; then
    set -- "-DBNG_OPTIMIZED_BUILD_TYPE=${BNG_OPTIMIZED_BUILD_TYPE}" "${@}"
  fi
  set -- -G="${CMAKE_GENERATOR}"  -DCMAKE_SYSTEM_NAME=iOS -DBNG_BUILD_TESTS=FALSE "${@}"
  if ! (cmake "${@}" -S src -B "${BUILD_DIR}"); then
    # if the failure is no CMAKE_CXX_COMPILER could be found try
    # sudo xcode-select --reset
    # per https://stackoverflow.com/questions/41380900/cmake-error-no-cmake-c-compiler-could-be-found-using-xcode-and-glfw
    # this step was required after first time installation of xcode.
    return 1
  fi
}

function run_cmake_build() {
  if [[ -n "${SDK_TARGET}" ]]; then
    set -- "${@}" -- -sdk "${SDK_TARGET}"
  fi  
  if ! cmake --build "${BUILD_DIR}" --parallel "${@}"; then
    echo "BUILD FAILED!" 1>&2    
    return 1
  fi
}

if [[ -n "${BUILD_IOS}" ]]; then
  ( BUILD_DIR=build_ios &&
    CMAKE_BUILD_TYPE="${BUILD_IOS}" &&
    run_cmake_gen "${@}" &&
    run_cmake_build )
fi

if [[ -n "${BUILD_IOS_SIM}" ]]; then
  ( BUILD_DIR=build_ios_simulator &&
    CMAKE_BUILD_TYPE="${BUILD_IOS_SIM}" &&
    VCPKG_TARGET_TRIPLET=arm64-ios-simulator &&
    SDK_TARGET=iphonesimulator &&
    BNG_OPTIMIZED_BUILD=BNG_DEBUG &&
    run_cmake_gen "${@}" &&
    run_cmake_build )
fi
