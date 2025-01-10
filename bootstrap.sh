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
    echo "to build with ninja use -G Ninja when running gen_desktop_project.sh"
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
    echo "python 3.11 required. ${PYTHON} is version ${PY_VER}" 1>&2
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
  python3 -m pip install pip --upgrade
  python3 -m pip install cyclopts pytest # requests numpy numpy-quaternion whatevs
else
  echo "existing python 3.11+ .venv found"
fi
echo "source .venv/.activate to use this virtual env python3"

echo "bootstrapping complete. project is ready to build."
