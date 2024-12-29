var words_url = "https://raw.githubusercontent.com/benn-herrera/letterboxed/refs/heads/main/src/letterboxed/words_alpha.txt"

class SolverType {
  static Javascript = "javascript"
  static Wasm = "wasm"
}

var ready_count = 0

function assert(cond, msg) {
  if (!cond) {
    alert("ASSERT FAILURE" + (msg != null ? (": " + msg) : ""))
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

function solver_init(on_ready) {
  let on_core_ready = function() {
    ++ready_count
    if (ready_count == 2 && on_ready != null) {
      on_ready()
    }
  }

  hit_url(
    words_url,
    function(response_text) {
      let word_list = response_text.split(/\r\n|\n/)
      js_core_init(word_list, on_core_ready)
      wasm_core_init(word_list, on_core_ready)
    }
  )
}

function solver_solve_puzzle(solver_type, box) {
  assert(box.length == 15 && box[3] == ' ' && box[7] == ' ' && box[11] == ' ', "invalid puzzle " + box)

  if (solver_type == SolverType.Wasm) {
    return wasm_core_solve(box)
  }

  return js_core_solve(box)
}
