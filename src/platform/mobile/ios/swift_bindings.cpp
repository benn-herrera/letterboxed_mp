#include "api/engine_api.h"
#include "platform/mobile/mobile.h"
#include "core/core.h"

// API functions from dependency libraries get dead stripped unless we force a reference.
API_EXPORT void* bng_forced_api_refs[] = {
  (void*)bng_engine_create,
  (void*)bng_engine_setup,
  (void*)bng_engine_solve,
  (void*)bng_engine_destroy
};

extern "C" {
  // add any swift-specific bindings here
  // API_EXPORT int bng_engine_foo_swift() { return 0; }
}
