#!/usr/bin/env bash
THIS_DIR=$(dirname "${0}")
# can't rely on realpath existing
THIS_DIR=$(cd "${THIS_DIR}"; pwd)

cd "${THIS_DIR}"

case "$(uname)" in
  MINGW*) IS_WIN=true;;
  Darwin*) IS_MAC=true;;
  Linux*) IS_LNX=true;;
  *) echo "unsupported platform $(uname)" 1>&2; exit 1;;
esac

if ! CMAKE=$(which cmake 2> /dev/null); then
  echo "cmake must be in path." 1>&2
  exit 1
fi
echo "cmake found."

if NINJA=$(which ninja 2> /dev/null); then
  echo "ninja found."
  if ${IS_WIN:-false}; then
    echo "to build with ninja set envar CMAKE_GENERATOR to \"Ninja Multi-Config\" when running gen_desktop_project.sh"
  fi
elif ${IS_LNX:-false}; then
  echo "ninja must be in path." 1>&2
  exit 1
else
  echo "ninja not in path. building with ninja will not be available."
fi

if [[ ! -f .venv/.activate ]]; then
  if ! PYTHON=$(which python3 2> /dev/null); then
    if ! PYTHON=$(which python 2> /dev/null); then
      echo "python3 or python must be in path with version >= 3.11" 1>&2
      exit 1
    fi
  fi
  PY_VER=$(${PYTHON} --version | awk '{print $2;}')
  PY_VER=${PY_VER%.*}
  PY_MAJ_VER=${PY_VER%.*}
  PY_MIN_VER=${PY_VER/*./}
  if [[ ${PY_MAJ_VER:-0} -lt 3 || ${PY_MIN_VER:-0} -lt 11 ]]; then
    echo "python 3.11+ required. ${PYTHON} is version ${PY_VER}" 1>&2
    exit 1
  fi
  echo "python ${PY_VER} found."
  if [[ ! -d .venv ]]; then
    ${PYTHON} -m venv .venv
  fi
  if ${IS_WIN:-false}; then
    ACTIVATE="${THIS_DIR}/.venv/Scripts/activate"
  else
    ACTIVATE="${THIS_DIR}/.venv/bin/activate"
  fi
  echo "source \"${ACTIVATE}\"" > .venv/.activate
  source .venv/.activate
  pip install pip --upgrade
  pip install -r "./src/tool_scripts/requirements.txt"
else
  echo "existing python 3.11+ .venv found"
fi
echo "source .venv/.activate to use this virtual env python3"

# allow system emscripten (for now)
if ! (which emsdk 2>&1) > /dev/null; then
  if [[ -d ./src/third_party/emsdk ]]; then
    source ./src/third_party/emsdk/emsdk_env.sh > /dev/null || exit 1
  fi
fi
if ! (which emsdk 2>&1) > /dev/null; then
  mkdir -p ./src/third_party
  (
    cd ./src/third_party &&
    git clone https://github.com/emscripten-core/emsdk.git &&
    cd emsdk &&
    ./emsdk install latest &&
    ./emsdk activate latest
  ) && source ./src/third_party/emsdk/emsdk_env.sh > /dev/null || exit 1

  echo "installed emscripten"
  echo "  $(em++ --version | head -1)"    
else
  echo "existing emscripten found"
  echo "  $(em++ --version | head -1)"
fi

"${THIS_DIR}"/util_scripts/git_pre_commit_hook.sh install

echo "bootstrapping complete. project is ready to build."
