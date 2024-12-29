#!/usr/bin/env bash
THIS_DIR=$(dirname "$0")
THIS_DIR=$(cd "${THIS_DIR}"; pwd)
cd "${THIS_DIR}"

IP_ADDR=0.0.0.0
PORT=8888

case "$(uname)" in
  Darwin) IP_ADDR=$(ipconfig getifaddr en0);;
  *) echo 'TODO: add linux and windows ip address getters.' 1>&2;;
esac

echo "serving ${THIS_DIR} at http://${IP_ADDR}:${PORT}"

python3 -m http.server ${PORT}
