#include "api/engine_api.h"
#include "platform/mobile/mobile.h"
#include "core/core.h"

#define BNG_ENGINE_API_FUNC_REF(FUNC) (void*)FUNC,

// API functions from dependency libraries get dead stripped unless we force a reference.
BNG_API_EXPORT void* bng_forced_api_refs[] = {
  BNG_ENGINE_API_FUNC_REFS
};

extern "C" {
  // add any swift-specific bindings here
  // BNG_API_EXPORT int bng_engine_foo_swift() { return 0; }
}
