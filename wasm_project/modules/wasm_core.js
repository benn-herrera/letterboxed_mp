// HAZARD: DO NOT USE IMPORT MAP
import { assert } from "/modules/common.js"
import createBngWasmModule from "/modules/bng.js"

var wasm_module = null
var engine_handle = null

function wasm_core_init(word_list, on_ready) {
  if (engine_handle != null) {
    engine_handle.delete()
    engine_handle = null
  }

  createBngWasmModule().then((inst) => {
    wasm_module = inst
    engine_handle = new wasm_module.EngineInterface()
    let setup_data = {wordsPath: "", cachePath: "", wordsData: word_list}
    let err_msg = engine_handle.setup(setup_data)
    if (!err_msg) {
      on_ready()
    }
    else {
      assert(false, err_msg)
    }
  })
}

function wasm_core_solve(box) {
  assert(engine_handle != null, "wasm_core_init() not completed.")
  let puzzle = {sides: [
      box.slice(0, 3),
      box.slice(4, 7),
      box.slice(8, 11),
      box.slice(12, 15)
    ]}
  return engine_handle.solve(puzzle)
}

const WasmCore = { init: wasm_core_init, solve: wasm_core_solve }
export default WasmCore
