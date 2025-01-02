#include "api/engine_api.h"
#include "platform/mobile/mobile.h"
#include "core/core.h"

extern "C" {
  // add any swift-specific bindings here
  API_EXPORT void force_references() {
    (void)bng_engine_create();
    (void)bng_engine_destroy(0);
    (void)bng_engine_setup(0, nullptr);
    (void)bng_engine_solve(0, nullptr);
  }
}
