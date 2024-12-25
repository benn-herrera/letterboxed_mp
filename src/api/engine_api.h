#pragma once

#include "engine_types.h"
#include "api_util.h"

#if defined(__cplusplus)
extern "C" {
#endif

API_EXPORT void bng_engine_hello(BngEngineThing*);

API_EXPORT int solve(int argc, const char *argv[]);

#if defined(__cplusplus)
}
#endif
