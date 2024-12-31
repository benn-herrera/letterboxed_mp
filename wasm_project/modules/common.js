class SolverType {
  static Javascript = "javascript"
  static Wasm = "wasm"
}

function assert(cond, msg) {
  if (!cond) {
    msg = "ASSERT FAILURE" + (msg != null ? (": " + msg) : "")
    console.error(msg)
    if (typeof alert != "undefined") {
      alert(msg)
    }
  }
}

function hit_url(url, on_response) {
  var request = new XMLHttpRequest()
  request.timeout = 3000
  request.open('GET', url, true)
  request.ontimeout = function() {
  }
  request.onload = function() {
    on_response(request.responseText)
  }
  request.send(null);    
}

const Common = { assert: assert, hit_url: hit_url, SolverType: SolverType }
export { assert, hit_url, SolverType }
export default Common
