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
usage: ${THIS_SCRIPT} [--help] | [--clean] [--build] [--test] [cmake_arg1]...
    note: bootstrap.sh must have been run first.
    --build: build after generating project
    --test: build and run tests after generating project. exit status reflects test result.
    --clean: delete build directory first
    any cmake args must come after --clean, --build.
    src/cmake/options.cmake:
    $(awk '{ print (NR == 1 ? "" : "    ") $0 }' "${THIS_DIR}/src/cmake/options.cmake")
__EOF
  exit ${1:-0}
}

cd "${THIS_DIR}"
if ! [[ -f .venv/.activate ]]; then
  echo "build environment not set up. running bootstrap.sh first."
  ./bootstrap.sh || exit 1
fi

# respect envars
BUILD=${BUILD:-false}
CMAKE_TOOLCHAIN_FILE=${TOOLCHAIN_FILE:-}
GEN_CLEAN=${GEN_CLEAN:-false}
TEST=${TEST:-false}

IS_LNX=false
IS_MAC=false
IS_WIN=false

case "$(uname)" in
  Linux*) IS_LNX=true; CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Ninja Multi-Config"};;
  Darwin*) IS_MAC=true; CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Ninja Multi-Config"};;
  MINGW*) IS_WIN=true; CMAKE_GENERATOR=${CMAKE_GENERATOR:-};;
  *) echo "unsupported platform $(uname)" 1>&2; exit 1;;
esac

if ! ${IS_WIN}; then
  # c compiler may default to gcc. ensure we're all clang all the time
  export CC=$(which clang)
fi

# stupid pet trick. support ninja build on windows.
if ${IS_WIN} && is_in Ninja "${CMAKE_GENERATOR}" && ! is_in --msvc "${*}"; then
  _SHELL=$(cygpath -w "${SHELL}")
  _VCVARS=$(echo "C:/Program Files/Microsoft Visual Studio"/*/*/VC/Auxiliary/Build/vcvars64.bat | tail -1)
  _VCVARS=$(cygpath -w "${_VCVARS}")
  script=$(cat << __EOF
    call "${_VCVARS}"
    "${_SHELL}" "${THIS_DIR}/${THIS_SCRIPT}" --msvc ${@}
__EOF
  )
  exec cmd <<< "${script}"
fi

while [[ -n "${1}" ]]; do
  case "${1}" in
    -h*|--h*|-u*|--u*) usage_and_die;;
    --clean|-c) GEN_CLEAN=true; shift;;
    --build|-b) BUILD=true; shift;;
    --test|-t) TEST=true; shift;;
    --msvc) shift;;
    *) break;;
  esac
done

if ${TEST}; then
  BUILD=true
fi

BUILD_DIR=build_desktop

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

  if [[ -n "${CMAKE_GENERATOR}" ]]; then
    set -- "-G=${CMAKE_GENERATOR}" "${@}"
  fi
  if ${TEST}; then
    set -- "${@}" -DBNG_BUILD_TESTS=TRUE
  fi
  if [[ -n "${CMAKE_TOOLCHAIN_FILE}" ]]; then
    set -- "-DCMAKE_TOOLCHAIN_FILE=${CMAKE_TOOLCHAIN_FILE}" "${@}"
  fi
  # set -- "${@}" -DBNG_OPTIMIZED_BUILD_TYPE=BNG_DEBUG
  if ! (cmake "${@}" -S src -B "${BUILD_DIR}"); then
    # if running on macos and the failure is no CMAKE_CXX_COMPILER could be found try
    # sudo xcode-select --reset
    # per https://stackoverflow.com/questions/41380900/cmake-error-no-cmake-c-compiler-could-be-found-using-xcode-and-glfw
    # this step was required after first time installation of xcode.
    return 1
  fi
}

function run_cmake_build() {
  if ! ${BUILD}; then
    return 0
  fi
  if ! cmake --build "${BUILD_DIR}" --parallel; then
    echo "BUILD FAILED!" 1>&2    
    return 1    
  fi
  if ${TEST}; then
    if ! cmake --build "${BUILD_DIR}" --parallel --config RelWithDebInfo; then
      echo "BUILD FAILED!" 1>&2    
      return 1    
    fi
  fi  
}

function run_cmake_test() {
  if ! ${TEST}; then
    return 0
  fi
  if ! cmake --build "${BUILD_DIR}" --parallel --target RUN_ALL_TESTS; then
    echo "TESTS FAILED!" 1>&2
    return 1
  fi
  (
    source ./.venv/.activate &&
    cd "src/tool_scripts" &&
    PYTHONPATH="$(pwd)" pytest
  ) || exit 1
  echo "test suites all passed."
}

run_cmake_gen "${@}" && \
  run_cmake_build && \
  run_cmake_test
