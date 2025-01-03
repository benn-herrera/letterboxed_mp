#include "engine.h"
#include "api/engine_api.h"

#if !defined(BNG_IS_WASM)
extern "C" {
  #define bng_make_api_strdup strdup
#endif

BNG_API_EXPORT BngEngineHandle bng_engine_create() {
  return (BngEngineHandle)new bng::engine::Engine;
}

BNG_API_EXPORT BNG_API_STRING bng_engine_setup(BngEngineHandle engine, const BNG_API_STRUCT_REF(BngEngineSetupData) setup_data) {
  auto sptr = &BNG_API_DEREF_STRUCT(setup_data);
  BNG_VERIFY(sptr && engine, "invalid engine or setup data!");
  if (!engine) {
    return bng_make_api_string("invalid engine!");
  }
  if (!sptr) {
    return bng_make_api_string("ERROR: invalid setup data!");
  }
  auto errMsg = ((bng::engine::Engine*)engine)->setup(BNG_API_DEREF_STRUCT(setup_data));
  return errMsg.empty() ? nullptr : strdup(errMsg.c_str());
}

BNG_API_EXPORT BNG_API_STRING bng_engine_solve(BngEngineHandle engine, const BNG_API_STRUCT_REF(BngEnginePuzzleData) puzzle) {
  auto pptr = &BNG_API_DEREF_STRUCT(puzzle);
  BNG_VERIFY(engine && pptr, "invalid engine or puzzle!");
  if (!engine) {
    return bng_make_api_string("ERROR: invalid engine!");
  }
  if (!pptr) {
    return bng_make_api_string("ERROR: invalid puzzle!");
  }
  auto solutions = ((bng::engine::Engine*)engine)->solve(BNG_API_DEREF_STRUCT(puzzle));
  return !solutions.empty() ? bng_make_api_string(solutions.c_str()) : nullptr;
}

BNG_API_EXPORT void bng_engine_destroy(BngEngineHandle engine) {
  if (engine) {
    delete (bng::engine::Engine*)engine;
  }
}

#if !defined(BNG_IS_WASM)
} // extern "C"
#endif
