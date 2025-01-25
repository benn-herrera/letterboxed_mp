#!/usr/bin/env bash
THIS_SCRIPT=$(basename "${0}")
THIS_DIR=$(dirname "${0}")
# can't rely on realpath existing
THIS_DIR=$(cd "${THIS_DIR}"; pwd)

# testing vvv hack. do not commit uncommented
#set -- --clean "${@}"

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
# must use xcode for iOS and visionOS targets
CMAKE_GENERATOR=${CMAKE_GENERATOR:-"Xcode"}

if [[ "${BUILD_IOS}" == "None" ]]; then
  BUILD_IOS=
fi
if [[ "${BUILD_IOS_SIM}" == "None" ]]; then
  BUILD_IOS_SIM=
fi

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

if ! [[ -f .venv/.activate ]]; then
  echo "build environment not set up. running bootstrap.sh first."
  ./bootstrap.sh || exit 1
fi

export BNG_APPLE_DEV_TEAM_ID=${BNG_APPLE_DEV_TEAM_ID}
FRAMEWORK_NAME=bng
SP_DIR=${THIS_DIR}/swift_project
SP_LIB_NAME=lbsolverlib
SP_BRIDGE_NAME=bng_bridge
SP_BRIDGE_DIR=${SP_DIR}/${SP_LIB_NAME}/Sources/${SP_BRIDGE_NAME}
SP_BRIDGE_HEADER_DIR=${SP_BRIDGE_DIR}/include_internal
SP_BRIDGE_SWIFT_DIR=${SP_DIR}/${SP_LIB_NAME}/lbsolverlib


function find_dev_team_id() {
  local TEAM_TYPE=${1}
  local XCODE_PREFS_PLIST=${HOME}/Library/Preferences/com.apple.dt.Xcode.plist
  if [[ -f "${XCODE_PREFS_PLIST}" ]]; then
    (/usr/libexec/PlistBuddy -c 'print :IDEProvisioningTeams' "${XCODE_PREFS_PLIST}" | awk '
      /teamID/ { printf("%s ", $NF); }
      /teamType/ { print $NF }' | awk "/ ${TEAM_TYPE}/ { print \$1; }") 2> /dev/null
  fi
}

function init_dev_team_id() {
  if [[ -n "${BNG_APPLE_DEV_TEAM_ID}" ]]; then
    echo "Deav Team Id ${BNG_APPLE_DEV_TEAM_ID} configured from envar"
    return 0
  fi
  for TEAM_TYPE in Company Team; do
    export BNG_APPLE_DEV_TEAM_ID=$(find_dev_team_id ${TEAM_TYPE})
    if [[ -n "${BNG_APPLE_DEV_TEAM_ID}" ]]; then
      echo "${TEAM_TYPE} Dev Team ID ${BNG_APPLE_DEV_TEAM_ID} configured from xcode settings."
      return 0
    fi
  done
  echo "envar BNG_APPLE_DEV_TEAM_ID not set and not dev team id could be found in xcode settings." 1>&2
  return 1
}

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
  if [[ -n "${BNG_OPTIMIZED_BUILD_TYPE:-}" ]]; then
    set -- "-DBNG_OPTIMIZED_BUILD_TYPE=${BNG_OPTIMIZED_BUILD_TYPE}" "${@}"
  fi
  if [[ -n "${SP_BRIDGE_HEADER_DIR}" ]]; then
    set -- "-DSWIFT_BRIDGE_HEADER_DIR=${SP_BRIDGE_HEADER_DIR}" "${@}"    
  fi
  if [[ -n "${SP_BRIDGE_SWIFT_DIR}" ]]; then
    set -- "-DSWIFT_BRIDGE_SWIFT_DIR=${SP_BRIDGE_SWIFT_DIR}" "${@}"    
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
  (/bin/rm -rf "${SP_BRIDGE_HEADER_DIR}" 2>&1; exit 0) > /dev/null
  if ! cmake --build "${BUILD_DIR}" --target install; then
    echo "HEADERS INSTALL FAILED!" 1>&2    
    return 1
  fi
}

init_dev_team_id || exit 1

FRAMEWORKS=
IOS_FRAMEWORK=

if [[ -n "${BUILD_IOS}" ]]; then
  ( BUILD_DIR=build_ios &&
    CMAKE_BUILD_TYPE="${BUILD_IOS}" &&
    run_cmake_gen "${@}" &&
    run_cmake_build ) || exit 1
  IOS_FRAMEWORK="${THIS_DIR}/build_ios/platform/mobile/ios/${BUILD_IOS}-iphoneos/${FRAMEWORK_NAME}.framework"
  FRAMEWORKS="${FRAMEWORKS} -framework ${IOS_FRAMEWORK}"
fi

if [[ -n "${BUILD_IOS_SIM}" ]]; then
  ( BUILD_DIR=build_ios_simulator &&
    CMAKE_BUILD_TYPE="${BUILD_IOS_SIM}" &&
    SDK_TARGET=iphonesimulator &&
    BNG_OPTIMIZED_BUILD=BNG_DEBUG &&
    run_cmake_gen "${@}" &&
    run_cmake_build ) || exit 1

  IOS_DBG_FRAMEWORK="${THIS_DIR}/build_ios_simulator/platform/mobile/ios/${BUILD_IOS_SIM}-iphoneos/${FRAMEWORK_NAME}.framework"
  IOS_SIM_FRAMEWORK="${THIS_DIR}/build_ios_simulator/platform/mobile/ios/${BUILD_IOS_SIM}-iphonesimulator/${FRAMEWORK_NAME}.framework"
  # ios simulator builds generate both simulator and device frameworks.
  # if device build was not specified use the debug device framework
  if [[ ! -n "${IOS_FRAMEWORK}" ]]; then
    FRAMEWORKS="${FRAMEWORKS} -framework ${IOS_DBG_FRAMEWORK}"    
  fi
  FRAMEWORKS="${FRAMEWORKS} -framework ${IOS_SIM_FRAMEWORK}"
fi

if [[ -n "${FRAMEWORKS}" ]]; then
  XCF_NAME=${FRAMEWORK_NAME}.xcframework
  XCF_PATH=${SP_DIR}/${SP_LIB_NAME}/${XCF_NAME}

  (/bin/rm -rf "${XCF_PATH}" 2>&1; exit 0) > /dev/null
  (/bin/rm -rf "${XCF_PATH}.zip" 2>&1; exit 0) > /dev/null
  xcodebuild -create-xcframework ${FRAMEWORKS} -output "${XCF_PATH}" || exit 1
fi
