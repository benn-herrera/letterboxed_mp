// HAZARD: DO NOT USE IMPORT MAP
import { assert } from "/modules/common.js"
import createBngWasmModule from "/modules/bng.js"

var wasm_module = null
var engine_handle = null

function solve(puzzle) {
  return wasm_module.bng_engine_solve(engine_handle, puzzle)
}

function setup(word_list) {
  return wasm_module.bng_engine_setup(engine_handle, word_list)
}


function destroy() {
  if (engine_handle != null) {
    wasm_module.bng_engine_destroy(engine_handle)
    engine_handle = null
  }
}

function create() {
  engine_handle = wasm_module.bng_engine_create()
}

// use this to skip 16 bit to 8 bit strings
// https://cs-263-emscripten.readthedocs.io/en/latest/files.html
// FS.createDataFile("/", "file.txt", "File contents here", true, true);

function wasm_core_init(word_list, on_ready) {
  if (wasm_module != null) {
    assert(false, "wasm_core_init() already called.")
    return
  }
  createBngWasmModule().then((inst) => {
    assert(inst != null, "module initialization failed!")
    destroy()
    wasm_module = inst
    create()
    let err_msg = setup(word_list)
    if (err_msg) {
      alert(err_msg)
      return
    }
    if (on_ready != null) {
      on_ready()
    }
  })
}

function wasm_core_solve(puzzle) {
  assert(wasm_module != null, "wasm_core_init() not completed.")
  return solve(puzzle)
}

const WasmCore = { init: wasm_core_init, solve: wasm_core_solve }
export default WasmCore