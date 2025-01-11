#include "engine.h"

namespace bng::engine {
  using namespace bng::core;
  using namespace bng::word_db;

  namespace dtl {
    WordDB::SideSet init_sides(const BngEnginePuzzleData& puzzleData) {
      char* side_strs[] = {
        (char*)puzzleData.sides[0].data(),
        (char*)puzzleData.sides[1].data(),
        (char*)puzzleData.sides[2].data(),
        (char*)puzzleData.sides[3].data()
      };
      auto print_err = [&side_strs]() {
        BNG_PRINT("%s %s %s %s are not 4 sides of 3 unique letters.\n",
          side_strs[0], side_strs[1], side_strs[2], side_strs[3]);
      };

      WordDB::SideSet sides;

      for (uint32_t si = 0, all_letters = 0; si < 4; ++si) {
        auto& s = sides[si];
        auto side_str = side_strs[si];
        char side_lc[4] = {};
        if (strlen(side_str) != 3) {
          print_err();
          return {};
        }
        for (uint32_t i = 0; i < 3; ++i) {
          side_lc[i] = char(tolower(side_str[i]));
          // side has non alpha characters
          if (side_lc[i] < 'a' || side_lc[i] > 'z') {
            print_err();
            return {};
          }
        }
        s = Word(side_lc);
        if ((all_letters & uint32_t(s.letters))) {
          // sides have overlapping letters
          print_err();
          return {};
        }
        all_letters |= uint32_t(s.letters);
      }

      return sides;
    }
  }

  std::string Engine::setup(const BngEngineSetupData &setupData) {
    auto timer = BNG_SCOPED_TIMER("loaded words_alpha.pre");
    auto wordsPath = std::filesystem::path(setupData.wordsPath);
    auto preprocessedPath = std::filesystem::path(setupData.cachePath) / "words_alpha.pre";

    BNG_VERIFY(!wordDB, "setup already called.");

    if (!setupData.wordsData.empty()) {
      timer.setMessage("proccessed dictionary");
      wordDB.read_words(setupData.wordsData.c_str());
    }
    else if (!wordDB.load(preprocessedPath)) {
      timer.setMessage("proccessed dictionary -> words_alpha.pre");
      if (!wordDB.load(wordsPath)) {
        return "failed loading word list.";
      }
      wordDB.save(preprocessedPath);
    }

    return wordDB ? "" : "failed preloading words database";
  }

  std::string Engine::solve(const BngEnginePuzzleData& puzzleData) {
    if (!wordDB) {
      return "ERROR: setup not called.";
    }
    auto timer = BNG_SCOPED_TIMER("solve()");

    const WordDB::SideSet sides = dtl::init_sides(puzzleData);
    if (!sides[0]) {
      timer.cancel();
      return "ERROR: invalid puzzle.";
    }

    // eliminate non-candidates and solve
    auto puzzleWordDB = wordDB.culled(sides);
    SolutionSet solutions = puzzleWordDB.solve(sides);

    if (solutions.empty()) {
      return "";
    }

    solutions.sort(puzzleWordDB);

    std::string outBuf;

    {
      size_t bufSize = 0;
      for (auto s : solutions) {
        auto& a = *puzzleWordDB.word(s.a);
        auto& b = *puzzleWordDB.word(s.b);
        bufSize += a.length + b.length + 5 ; // " -> " + "\n";
      }
      outBuf.reserve(bufSize + 1);
    }

    {
      char line[80];
      for (auto ps : solutions) {
        auto& a = *puzzleWordDB.word(ps.a);
        auto& b = *puzzleWordDB.word(ps.b);
        if (a.letter_count == 12 || b.letter_count == 12) {
          auto& c = (a.letter_count == 12) ? a : b;
          snprintf(line, sizeof(line), "%.*s\n",
            uint32_t(c.length), puzzleWordDB.str(c));
        }
        else {
          snprintf(line, sizeof(line), "%.*s -> %.*s\n",
            uint32_t(a.length), puzzleWordDB.str(a), uint32_t(b.length), puzzleWordDB.str(b));
        }
        outBuf += line;
      }
    }

    return outBuf;
  }
}
