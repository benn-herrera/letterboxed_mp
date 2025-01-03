#pragma once

#include "core/core.h"
#include "word_db.h"
#include "api/engine_api.h"

namespace bng::engine {
    class Engine {
      BNG_DECL_NO_COPY(Engine)
      public:
        Engine() = default;
        std::string setup(const BngEngineSetupData& setupData);
        std::string solve(const BngEnginePuzzleData& puzzleData);

      private:
        word_db::WordDB wordDB;
    };
}
