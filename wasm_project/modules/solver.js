import { assert, hit_url } from "common"
import { js_core_init, js_core_solve } from "js_core"
import { wasm_core_init, wasm_core_solve } from "wasm_core"

const words_url = "https://raw.githubusercontent.com/benn-herrera/letterboxed/refs/heads/main/src/letterboxed/words_alpha.txt"

class SolverType {
  static Javascript = "javascript"
  static Wasm = "wasm"
}

var ready_count = 0

function solver_init(on_ready) {
  let on_core_ready = () => {
    ++ready_count
    console.log(`ready_count: ${ready_count}/2`)
    if (ready_count == 2 && on_ready != null) {
      on_ready()
    }
  }

  hit_url(
    words_url,
    (response_text) => {
      js_core_init(response_text, on_core_ready)
      wasm_core_init(response_text, on_core_ready)
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

export { solver_init, solver_solve_puzzle, SolverType }
