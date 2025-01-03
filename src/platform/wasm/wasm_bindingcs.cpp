#include "api/engine_api.h"
#include "engine/engine.h"
#include "core/core.h"

// TODO: struct bindings for BngEngineSetupData and BngEnginePuzzleData
// https://ninkovic.dev/blog/2022/an-improved-guide-for-compiling-wasm-with-emscripten-and-embind

std::string bng_engine_setup_simple(BngEngineHandle engine_handle, const std::string& words_text) {
  if (!engine_handle) {
    return "ERROR: invalid engine_handle!";
  }

  BngEngineSetupData setup_data{};
  setup_data.wordsData = words_text.c_str();

  return ((bng::engine::Engine*)engine_handle)->setup(setup_data);
}

std::string bng_engine_solve_simple(BngEngineHandle engine_handle, std::string box) {
  if (!engine_handle) {
    return "ERROR: invalid engine_handle!";
  }

  BngEnginePuzzleData puzzle{};
  box[3] = box[7] = box[11] = 0;
  puzzle.sides[0] = &box[0];
  puzzle.sides[1] = &box[4];
  puzzle.sides[2] = &box[8];
  puzzle.sides[3] = &box[12];

  return ((bng::engine::Engine*)engine_handle)->solve(puzzle);
}

std::string get_exception_message(intptr_t exceptionPtr) {
  return std::string(reinterpret_cast<std::exception *>(exceptionPtr)->what());
}

#include <emscripten/bind.h>
using namespace emscripten;

#define BNG_ENGINE_API_FUNC_REF(FUNC) function(BNG_STRINGIFY(FUNC), &FUNC);

EMSCRIPTEN_BINDINGS(bng) {
  function("getExceptionMessage", & get_exception_message);
  BNG_ENGINE_API_FUNC_REFS
  BNG_ENGINE_API_FUNC_REF(bng_engine_setup_simple)
  BNG_ENGINE_API_FUNC_REF(bng_engine_solve_simple)  
}