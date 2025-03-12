#!/usr/bin/env bash
HOOK="pre-commit"
BLACK_OPTIONS="--line-length=100"

THIS_SCRIPT=$(basename "${0}")
THIS_DIR=$(dirname "${0}")
THIS_DIR=$(cd "${THIS_DIR}"; pwd)

if [[ "${THIS_SCRIPT}" == "${HOOK}" ]]; then
  # running from installed location
  PROJECT_DIR=$(cd "${THIS_DIR}"; cd ../..; pwd)
  AS_INSTALLED=true
else
  # running from util_scripts/
  PROJECT_DIR=$(cd "${THIS_DIR}"; cd ..; pwd)
  AS_INSTALLED=false
fi

function make_symlink() {
  local src=${1}
  local dst=${2}

  case "$(uname)" in
    Linux|Darwin)
      ln -sv "${src}" "${dst}";;
    # MINGW*|MSYS*)
    *)
      local diropt
      src=$(cygpath -w "${src}")
      dst=$(cygpath -w "${dst}")

      if [[ -d "${src}" ]]; then
        diropt='/J'
      fi
      (cmd //C "mklink ${diropt} ${dst} ${src}");;
  esac
}

function install_hook() {
  local hook_file="${THIS_DIR}/${THIS_SCRIPT}"
  local target_hook="${PROJECT_DIR}/.git/hooks/${HOOK}"

  if [[ "${1}" == install ]]; then
    [[ -e "${target_hook}" ]] && echo "git ${HOOK} hook already installed." && return 0
    make_symlink "${hook_file}" "${target_hook}" && echo "installed git ${HOOK} hook."
  elif [[ "${1}" == uninstall ]]; then
    [[ ! -e "${target_hook}" ]] && echo "git ${HOOK} hook not installed." && return 0
    rm -vf "${target_hook}" && echo "uninstalled git ${HOOK} hook."
  fi
}

function auto_format_python() {
  cd "${PROJECT_DIR}"

  # https://stackoverflow.com/questions/33610682/git-list-of-staged-files
  local staged_python=$(git diff --name-only --cached | grep '.py$')
  [[ -n "${staged_python}" ]] || return 0

  source "./.venv/.activate"
  local reformatted=$(black ${BLACK_OPTIONS} ${staged_python} 2>&1 | awk '
    /^reformatted/ {
      # posixify windows path
      gsub(/\\/, "/", $NF);
      # make path relative to ${PROJECT_DIR}
      gsub(/^.*\/src\//, "src/", $NF)
      print $NF;
    }
  ')
  [[ -n "${reformatted}" ]] || return 0

  echo "#############################################################"
  echo "# ${HOOK} hook reformatted and re-added python file(s):"
  git add -v ${reformatted} 2>&1 | awk '{ gsub(/^add /, "# "); print($0); }'
  echo "# please re-run git commit."
  echo "#############################################################"
  exit 1
}

if ${AS_INSTALLED}; then
  auto_format_python "${@}"
else
  install_hook "${1:-install}"
fi
