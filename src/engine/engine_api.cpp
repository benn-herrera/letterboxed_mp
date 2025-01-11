#include "engine.h"
#include "api/engine_api.h"

#if 0
extern "C" {

BNG_API_EXPORT BngEngineHandle bng_engine_create() {
  return (BngEngineHandle)new bng::engine::Engine;
}

BNG_API_EXPORT char* bng_engine_setup(BngEngineHandle engine, const BngEngineSetupData* setup_data) {
  BNG_VERIFY(engine && setup_data, "invalid engine or setup data!");
  if (!engine) {
    return strdup("invalid engine!");
  }
  if (!setup_data) {
    return strdup("ERROR: invalid setup data!");
  }
  auto errMsg = ((bng::engine::Engine*)engine)->setup(*setup_data);
  return errMsg.empty() ? nullptr : strdup(errMsg.c_str());
}

BNG_API_EXPORT char* bng_engine_solve(BngEngineHandle engine, const BngEnginePuzzleData* puzzle) {
  BNG_VERIFY(engine && puzzle, "invalid engine or puzzle!");
  if (!engine) {
    return strdup("ERROR: invalid engine!");
  }
  if (!puzzle) {
    return strdup("ERROR: invalid puzzle!");
  }
  auto solutions = ((bng::engine::Engine*)engine)->solve(*puzzle);
  return !solutions.empty() ? strdup(solutions.c_str()) : nullptr;
}

BNG_API_EXPORT void bng_engine_destroy(BngEngineHandle engine) {
  if (engine) {
    delete (bng::engine::Engine*)engine;
  }
}

} // extern "C"

#endif // 0
