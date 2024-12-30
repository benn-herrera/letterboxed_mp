import { assert } from "common"
import createBngWasmModule from "bng_wasm"

var wasm_core = null
var wasm_module = null

class WasmCore {
  constructor() {
    this.engine_handle = wasm_module.bng_engine_create()
    assert(this.engine_handle != null && this.engine_handle != 0, "create failed!")
  }

  setup(word_list) {
    return wasm_module.bng_engine_setup(this.engine_handle, word_list)
  }

  solve(box) {
    return wasm_module.bng_engine_solve(this.engine_handle, box)
  }

  destroy() {
    wasm_module.bng_engine_destroy(this.engine_handle)
    this.engine_handle = 0
  }
}

// use this to skip 16 bit to 8 bit strings
// https://cs-263-emscripten.readthedocs.io/en/latest/files.html
// FS.createDataFile("/", "file.txt", "File contents here", true, true);

function wasm_core_init(word_list, on_ready) {
  let options = {}
  createBngWasmModule(options).then((inst) => {
    wasm_module = inst
    wasm_core = new WasmCore()
    let err_msg = wasm_core.setup(word_list)
    if (err_msg) {
      alert(err_msg)
      return
    }
    if (on_ready != null) {
      on_ready()
    }
  })
}

function wasm_core_solve(box) {
  assert(wasm_core != null, "wasm_core_init() not completed.")
  return wasm_core.solve(box)
}

export { wasm_core_init, wasm_core_solve }
