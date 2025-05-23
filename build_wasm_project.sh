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
usage: ${THIS_SCRIPT} [--help] | [--clean] [--release] [--debug] [cmake_arg1]...
    note: bootstrap.sh must have been run first.    
    --clean: delete build directory first
    --debug: build debug config (project is multiconfig)
    --release: build release config (project is multiconfig)
    any cmake args must come after --clean, --build.
    src/cmake/options.cmake:
    $(awk '{ print (NR == 1 ? "" : "    ") $0 }' "${THIS_DIR}/src/cmake/options.cmake")
__EOF
  exit ${1:-0}
}

IS_LNX=false
IS_MAC=false
IS_WIN=false

case "$(uname)" in
  Linux*) IS_LNX=true;;
  Darwin*) IS_MAC=true;;
  MINGW*) IS_WIN=true;;
  *) echo "unsupported platform $(uname)" 1>&2; exit 1;;
esac

# respect envars
RELEASE_BUILD_CONFIG=${RELEASE_BUILD_CONFIG:-Release}
BUILD_CONFIG=${BUILD_CONFIG:-Debug}
GEN_CLEAN=${GEN_CLEAN:-false}
WASM_INSTALL_DIR=${WASM_INSTALL_DIR:-${THIS_DIR}/wasm_project/modules}
#if ${IS_WIN}; then
#  CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Visual Studio 17 2022"}
#else
  CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Ninja Multi-Config"}  
#fi

while [[ -n "${1}" ]]; do
  case "${1}" in
    -h*|--h*|-u*|--u*) usage_and_die 0;;
    --clean|-c) GEN_CLEAN=true; shift;;
    --*debug) BUILD_CONFIG=Debug; shift;;
    --*release) BUILD_CONFIG=${RELEASE_BUILD_CONFIG}; shift;;
    *) break;;
  esac
done

cd "${THIS_DIR}"

if ! [[ -f .venv/.activate ]]; then
  echo "build environment not set up. running bootstrap.sh first."
  ./bootstrap.sh || exit 1
fi

if ! (which emcmake 2>&1) > /dev/null; then
  source ./src/third_party/emsdk/emsdk_env.sh > /dev/null || exit 1
fi

function run_cmake_gen() {
  if ${GEN_CLEAN}; then
    (/bin/rm -rf "${BUILD_DIR}" 2>&1) > /dev/null
  fi
  if [[ ! -d "${BUILD_DIR}" ]]; then
    mkdir "${BUILD_DIR}"
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
  if [[ -n "${WASM_INSTALL_DIR:-}" ]]; then
    set -- "-DBNG_WASM_INSTALL_DIR=${WASM_INSTALL_DIR}" "${@}"
  fi  
  set -- \
    -G="${CMAKE_GENERATOR}" \
    -DBNG_BUILD_TESTS=FALSE \
    -DBNG_RELEASE_BUILD_CONFIG=${RELEASE_BUILD_CONFIG} \
    "${@}"

  # https://stunlock.gg/posts/emscripten_with_cmake/#tldr
  if ! (emcmake cmake "${@}" -S src -B "${BUILD_DIR}"); then
    return 1
  fi
}

function run_cmake_build() {
  if [[ -n "${BUILD_CONFIG}" ]]; then
    if ! cmake --build "${BUILD_DIR}" --parallel --config=${BUILD_CONFIG}; then
      echo "BUILD ${BUILD_CONFIG} FAILED!" 1>&2    
      return 1
    fi
  fi
}

( BUILD_DIR=build_wasm &&
  run_cmake_gen "${@}" &&
  run_cmake_build )
