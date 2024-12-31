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

# https://www.frontendeng.dev/blog/38-disable-cache-for-python-http-server
NO_CACHE_SERVER_PY=$(
  cat << __EOF
import http.server
import socketserver
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

with socketserver.TCPServer(("", ${PORT}), MyHTTPRequestHandler) as httpd:
    httpd.serve_forever()
__EOF
)

python3 <<< "${NO_CACHE_SERVER_PY}"
