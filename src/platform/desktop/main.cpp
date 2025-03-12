#include "bng_api.h"
#include "core/core.h"

int main(int argc, const char *argv[]) {
    using namespace bng::engine;
    const char** side_args = &argv[1];
    auto side_count = argc - 1;

    if (side_count != 4) {
        BNG_PRINT("usage: <side> <side> <side> <side>\n  e.g. letterboxed vrq wue isl dmo\n");
        return 1;
    }

    auto cachePath = std::filesystem::path(argv[0]).parent_path();
    auto wordsPath = cachePath / "words_alpha.txt";

    auto solver = std::unique_ptr<EngineInterface>(EngineInterface::create());
    EngineSetupData setupData{};
    setupData.cachePath = cachePath.string();
    setupData.wordsPath = wordsPath.string();

    auto err = solver->setup(setupData);
    if (!err.empty()) {
        BNG_PRINT("%s\n", err.c_str());
        return 1;
    }

    EnginePuzzleData puzzleData{};
    for (auto& side: puzzleData.sides) {
        side = side_args[&side - &puzzleData.sides[0]];
    }

    auto solutions = solver->solve(puzzleData);
    if (strstr(solutions.c_str(), "ERROR")) {
        BNG_PRINT("%s\n", solutions.c_str());
        return 1;
    }
    const char* p = solutions.c_str();
    const char* end = p + solutions.size();
    BNG_PRINT("puzzle: %s %s %s %s\n",
        puzzleData.sides[0].c_str(),
        puzzleData.sides[1].c_str(),
        puzzleData.sides[2].c_str(),
        puzzleData.sides[3].c_str());
    BNG_PRINT("solutions\n=============\n");
    while (p < end) {
        if (const char* pnext = strstr(p, "\n")) {
            ++pnext;
            BNG_PRINT("%.*s", uint32_t(pnext - p), p);
            p = pnext;
        } else {
            break;
        }
    }

    return 0;
}
