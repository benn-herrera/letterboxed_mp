#pragma once

#include "engine_types.h"
#include "api_util.h"

#if defined(BNG_ENGINE_IMPL)
# define BNG_ENGINE_API BNG_API_EXPORT
#else
# define BNG_ENGINE_API BNG_API_IMPORT
#endif

#if defined(__cplusplus)
extern "C" {
#endif

  BNG_ENGINE_API BngEngineHandle bng_engine_create();

  // CONTRACT: char* buffer ownersip passes to caller. must be released with free()

  BNG_ENGINE_API char* bng_engine_setup(BngEngineHandle, const BngEngineSetupData*);

  BNG_ENGINE_API char* bng_engine_solve(BngEngineHandle, const BngEnginePuzzleData*);

  BNG_ENGINE_API void bng_engine_destroy(BngEngineHandle);

#if defined(__cplusplus)
}
#endif
