var wasm_core = null

// https://stackoverflow.com/questions/46815205/how-to-pass-a-string-to-c-code-compiled-with-emscripten-for-webassembly

class WasmCore {
  constructor(module_exports, word_list) {
    this.create_wasm = module_exports.bng_engine_create
    this.setup_wasm = module_exports.bng_engine_setup_wasm    
    this.solve_wasm = module_exports.bng_engine_solve_wasm
    this.destroy_wasm = module_exports.bng_engine_destroy
    this.free_string_wasm = module_exports.bng_engine_free_string_wasm
    this.engine_handle = 0

    assert(this.create_wasm != null, "create_wasm not bound!")
    assert(this.setup_wasm != null, "setup_wasm not bound!")
    assert(this.solve_wasm != null, "solve_wasm not bound!")
    assert(this.free_string_wasm != null, "free_string_wasm not bound!")    
    assert(this.destroy_wasm != null, "destroy_wasm not bound!")

    this.create()
    this.setup(word_list)
  }

  create() {
    this.engine_handle = this.create_wasm()
    assert(this.engine_handle != null && this.engine_handle != 0, "create failed!")
  }

  setup(word_list) {
    return this._use_ptr_ret_ptr(word_list, function(ptr) {
      return this.setup_wasm(this.engine_handle, ptr)
    })
  }

  solve(box) {
    return this._use_ptr_ret_ptr(box, function(ptr) {
      return this.solve_wasm(this.engine_handle, ptr)
    })
  }

  destroy() {
    this.destroy_wasm(this.engine_handle)
    this.engine_handle = 0
  }

  _use_ptr(text, lambda) {
    let ptr = allocate(intArrayFromString(text), 'i8', ALLOC_NORMAL)
    try {
      let rv = lambda(ptr)
    } catch(error) {
      alert(error)
    }
    _free(ptr)
    return rv
  }

  _use_ptr_ret_ptr(text, lambda) {
    let wasm_rv = this._use_ptr(text, lambda)
    if (wasm_rv != null) {
      let rv = Pointer_stringify(wasm_rv)
      this.free_string_wasm(wasm_rv)
      return rv
    }
    return null
  }
}

function wasm_core_init(word_list, on_ready) {
  // https://stunlock.gg/posts/emscripten_with_cmake/#tldr
  WebAssembly.instantiateStreaming(
    fetch('solver_cores/bng.wasm'),
  ).then(result => {
    wasm_core = new WasmCore(result.instance.exports, word_list)
    if (on_ready != null) {
      on_ready()
    }
  });
}

function wasm_core_solve(box) {
  assert(wasm_core != null, "wasm_core_init() not completed.")
  return wasm_core.solve(box)
}
