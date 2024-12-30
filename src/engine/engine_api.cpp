#include "engine.h"
#include "api/engine_api.h"

extern "C" {
  API_EXPORT BngEngineHandle bng_engine_create() {
    return (BngEngineHandle)new bng::engine::Engine;
  }

  API_EXPORT char* bng_engine_setup(BngEngineHandle engine, const BngEngineSetupData* setupData) {
    BNG_VERIFY(engine, "invalid engine!");
    if (!engine) {
      return bng_strdup("invalid engine!");
    }
    auto errMsg = ((bng::engine::Engine*)engine)->setup(*setupData);
    return errMsg.empty() ? nullptr : bng_strdup(errMsg.c_str());
  }

  API_EXPORT char* bng_engine_solve(BngEngineHandle engine, const BngEnginePuzzleData* puzzle) {
    BNG_VERIFY(engine && puzzle, "invalid engine or puzzle!");
    if (!engine) {
      return bng_strdup("ERROR: invalid engine!");
    }
    if (!puzzle) {
      return bng_strdup("ERROR: invalid puzzle!");
    }
    auto solutions = ((bng::engine::Engine*)engine)->solve(*puzzle);
    return !solutions.empty() ? bng_strdup(solutions.c_str()) : nullptr;
  }

  API_EXPORT void bng_engine_destroy(BngEngineHandle engine) {
    if (engine) {
      delete (bng::engine::Engine*)engine;
    }
  }
}
