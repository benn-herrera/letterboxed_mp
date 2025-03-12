#pragma once

#include "core/core.h"
#include "word_db.h"

// generated header that defines the common data structures plus the interface we have to implement
#include "bng_api.h"

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
