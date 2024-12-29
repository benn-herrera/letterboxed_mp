  // TODO: replace with wasm solver
var wasm_core = null

class WasmCore {
  constructor(word_list) {
    this.word_list = word_list
  }
}

function wasm_core_init(word_list) {
  wasm_core = new WasmCore(word_list)
}

function wasm_core_solve(box) {
  assert(wasm_core != null, "wasm_core_init() not called.")
  return js_core_solve(box)
}
