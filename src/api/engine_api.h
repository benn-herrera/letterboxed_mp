#pragma once

#include "engine_types.h"
#include "api_util.h"

#if defined(BNG_ENGINE_IMPL)
# define BNG_ENGINE_API BNG_API_EXPORT
#else
# define BNG_ENGINE_API BNG_API_IMPORT
#endif

#if defined(__cplusplus) && !defined(BNG_IS_WASM)
extern "C" {
#endif

  BNG_ENGINE_API BngEngineHandle bng_engine_create();

  BNG_ENGINE_API BNG_API_STRING bng_engine_setup(BngEngineHandle, const BNG_API_STRUCT_REF(BngEngineSetupData));

  BNG_ENGINE_API BNG_API_STRING bng_engine_solve(BngEngineHandle, const BNG_API_STRUCT_REF(BngEnginePuzzleData));

  BNG_ENGINE_API void bng_engine_destroy(BngEngineHandle);

#if defined(__cplusplus) && !defined(BNG_IS_WASM)
}
#endif

// provide a macro for manipulating the api function list.
// useful for forcing references or binding
#define BNG_ENGINE_API_FUNC_REFS \
  BNG_ENGINE_API_FUNC_REF(bng_engine_create) \
  BNG_ENGINE_API_FUNC_REF(bng_engine_setup) \
  BNG_ENGINE_API_FUNC_REF(bng_engine_solve) \
  BNG_ENGINE_API_FUNC_REF(bng_engine_destroy)