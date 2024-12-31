// HAZARD: DO NOT USE IMPORT MAP
import { SolverType } from "/modules/common.js"
import JSCore from "/modules/js_core.js"
import WasmCore from "/modules/wasm_core.js"

var ready_count = 0

function solve(solver_type, puzzle) {
  var solve_ms = performance.now()
  let solutions = (solver_type == SolverType.Wasm) ? WasmCore.solve(puzzle) : JSCore.solve(puzzle)
  solve_ms = performance.now() - solve_ms
  return {solutions: solutions, solve_ms: solve_ms}
}

self.onmessage = (e) => {
  let message = e.data
  self.postMessage(`handshake: ${message}`)
  if (typeof message == "string") {
    return
  }
  if (message.type == "init") {
    let words_text = message.arguments.words_text
    let on_core_ready = () => {
        ++ready_count
        console.log(`ready_count: ${ready_count}/2`)
        if (ready_count == 2) {
          self.postMessage({
            type: message.type,
            results: true
          })
        }
      }
    JSCore.init(words_text, on_core_ready)
    WasmCore.init(words_text, on_core_ready)
  }

  if(message.type == "solve") {
    self.postMessage({
      type: message.type, 
      results: solve(message.arguments.solver_type, message.arguments.puzzle)
    })
  }
}
