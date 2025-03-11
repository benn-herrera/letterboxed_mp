#pragma once

#include "core/core.h"
#include "word_db.h"

// include generated header.
#include "gen/bng_api.h"

namespace bng::engine {
  class Engine : public EngineInterface {
    BNG_DECL_NO_COPY(Engine)
    public:
      Engine() = default;
      std::string setup(const EngineSetupData& setupData) override;
      std::string solve(const EnginePuzzleData& puzzleData) override;

    private:
      word_db::WordDB wordDB;
  };
}
// transitional to help get stuff building
using BngEngineSetupData = bng::engine::EngineSetupData;
using BngEnginePuzzleData = bng::engine::EnginePuzzleData;
