// HAZARD: DO NOT USE IMPORT MAP
import { assert } from "/modules/common.js"
import createBngWasmModule from "/modules/bng.js"

var wasm_module = null
var engine_handle = null

function wasm_core_init(word_list, on_ready) {
  if (engine_handle != null) {
    wasm_module.bng_engine_destroy(engine_handle)
    engine_handle = null
  }
  createBngWasmModule().then((inst) => {
    wasm_module = inst
    engine_handle = wasm_module.bng_engine_create()
    let err_msg = wasm_module.bng_engine_setup_simple(engine_handle, word_list)
    if (!err_msg) {
      on_ready()
    }
    else {
      assert(false, err_msg)
    }
  })
}

function wasm_core_solve(puzzle) {
  assert(engine_handle != null, "wasm_core_init() not completed.")
  return wasm_module.bng_engine_solve_simple(engine_handle, puzzle)
}

const WasmCore = { init: wasm_core_init, solve: wasm_core_solve }
export default WasmCore