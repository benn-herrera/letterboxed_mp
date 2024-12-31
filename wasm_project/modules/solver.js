import { assert, hit_url } from "/modules/common.js"
const words_url = "https://raw.githubusercontent.com/benn-herrera/letterboxed/refs/heads/main/src/letterboxed/words_alpha.txt"

var solver_worker = null
var on_solved = null

function solver_init(on_ready) {
  console.log("solver_init()")

  assert(solver_worker == null, "already initialized")

  solver_worker = new Worker("modules/solver_worker.js", {type: "module"})
  console.log("worker created.")

  solver_worker.onmessage = (e) => {
    let message = e.data
    console.log(`solver received: ${message}`)
    if (typeof message == "string") {
      return
    }
    if (message.type == "init") {
      on_ready(message.results)
      return
    }
    if (message.type == "solve") {
      on_solved(message.results.solutions, message.results.solve_ms)
      on_solved = null
      return
    }
  }
  console.log("handler added.")
  solver_worker.postMessage("ping")

  hit_url(words_url, (response_text) => {
    console.log("solver_init() posting init message to worker")
    solver_worker.postMessage({
      type: "init", arguments: {words_text: response_text}
    })
  })
}

function solver_solve_puzzle(solver_type, puzzle, solved_callback) {
  assert(solver_worker != null, "not initialized")
  assert(puzzle.length == 15 && puzzle[3] == ' ' && puzzle[7] == ' ' && puzzle[11] == ' ', "invalid puzzle " + puzzle)
  if (on_solved != null) {
    solved_callback("ERROR: still solving last puzzle.")
    return
  }
  on_solved = solved_callback
  solver_worker.postMessage({
    type: "solve", 
    arguments: {
      solver_type: solver_type, 
      puzzle: puzzle
    }
  })
}

const Solver = {init: solver_init, solve_puzzle: solver_solve_puzzle }
export { solver_init, solver_solve_puzzle }
export default Solver
