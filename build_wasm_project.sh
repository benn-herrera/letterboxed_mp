#!/usr/bin/env bash -x
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
usage: ${THIS_SCRIPT} [--help] | [--clean] [--build-release] [--build-debug] [cmake_arg1]...
    note: bootstrap.sh must have been run first.    
    --clean: delete build directory first
    any cmake args must come after --clean, --build.
    src/cmake/options.cmake:
    $(awk '{ print (NR == 1 ? "" : "    ") $0 }' "${THIS_DIR}/src/cmake/options.cmake")
__EOF
  exit ${1:-0}
}


# respect envars
BUILD_DEBUG=${BUILD_DEBUG:-true}
BUILD_RELEASE=${BUILD_RELEASE:-false}
GEN_CLEAN=${GEN_CLEAN:-false}
CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Ninja Multi-Config"}

IS_LNX=false
IS_MAC=false
IS_WIN=false

case "$(uname)" in
  Linux*) IS_LNX=true;;
  Darwin*) IS_MAC=true;;
  MINGW*) IS_WIN=true;;
  *) echo "unsupported platform $(uname)" 1>&2; exit 1;;
esac

while [[ -n "${1}" ]]; do
  case "${1}" in
    -h*|--h*|-u*|--u*) usage_and_die;;
    --clean|-c) GEN_CLEAN=true; shift;;
    --build-debug) BUILD_DEBUG=true; shift;;
    --build-release) BUILD_RELEASE=true; shift;;
    *) break;;
  esac
done

cd "${THIS_DIR}"

if ! [[ -f .venv/.activate ]]; then
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

  if [[ -n "${BNG_OPTIMIZED_BUILD_TYPE:-}" ]]; then
    set -- "-DBNG_OPTIMIZED_BUILD_TYPE=${BNG_OPTIMIZED_BUILD_TYPE}" "${@}"
  fi
  set -- -G="${CMAKE_GENERATOR}" -DBNG_BUILD_TESTS=FALSE "${@}"
  if ! (emcmake cmake "${@}" -S src -B "${BUILD_DIR}"); then
    # if running on macos and the failure is no CMAKE_CXX_COMPILER could be found try
    # sudo xcode-select --reset
    # per https://stackoverflow.com/questions/41380900/cmake-error-no-cmake-c-compiler-could-be-found-using-xcode-and-glfw
    # this step was required after first time installation of xcode.
    return 1
  fi
}

function run_cmake_build() {
  if ${BUILD_DEBUG}; then
    if ! cmake --build "${BUILD_DIR}" --parallel --config=Debug "${@}"; then
      echo "BUILD DEBUG FAILED!" 1>&2    
      return 1
    fi
  fi
  if ${BUILD_RELEASE}; then
    if ! cmake --build "${BUILD_DIR}" --parallel --config=RelWithDebInfo "${@}"; then
      echo "BUILD RELEASE FAILED!" 1>&2    
      return 1
    fi
  fi
}

( BUILD_DIR=build_wasm &&
  run_cmake_gen "${@}" &&
  run_cmake_build )
