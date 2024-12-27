#pragma once

#include "engine_types.h"
#include "api_util.h"

#if defined(__cplusplus)
extern "C" {
#endif
  API_EXPORT BngEngine* bng_engine_create();

  // contract: returned memory buffer ownership passes to caller.
  //           must release with free()
  API_EXPORT char* bng_engine_setup(BngEngine*, const BngEngineSetupData*);

  // contract: returned memory buffer ownership passes to caller.
  //           must release with free()
  API_EXPORT char* bng_engine_solve(BngEngine*, const BngEnginePuzzleData*);

  API_EXPORT void bng_engine_destroy(BngEngine*);
#if defined(__cplusplus)
}
#endif
