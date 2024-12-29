#include "wasm.h"
#include "api/engine_api.h"
#include "core/core.h"

extern "C" {
  API_EXPORT char* bng_engine_setup_wasm(BngEngineHandle engine_handle, const char* words_text) {
    BngEngineSetupData setup_data{};
    setup_data.wordsData = words_text;
    return bng_engine_setup(engine_handle, &setup_data);
  }

  API_EXPORT char* bng_engine_solve_wasm(BngEngineHandle engine_handle, const char* box) {    
    char sides[32] = {};
    BngEnginePuzzleData puzzle{};

    strncpy(sides, box, sizeof(sides));
    sides[3] = sides[7] = sides[11] = 0;
    puzzle.sides[0] = sides;
    puzzle.sides[1] = sides + 4;
    puzzle.sides[2] = sides + 8;
    puzzle.sides[3] = sides + 12;
    
    return bng_engine_solve(engine_handle, &puzzle);
  }

  API_EXPORT void bng_engine_free_string_wasm(char* ptr) {
    if (ptr) {
      free(ptr);
    }
  }
}