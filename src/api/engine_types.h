#pragma once

#if defined(__cplusplus)
extern "C" {
#endif

  // const char* buffer ownership not transferred
  // source buffers only guaranteed to exist for duration of synchronous API call.

  struct BngEngineSetupData {
    const char* cachePath;
    const char* wordsPath;
  };
  typedef struct BngEngineSetupData BngEngineSetupData;

  struct BngEnginePuzzleData {
    const char* sides[4];
  };

  typedef struct BngEngine BngEngine;

#if defined(__cplusplus)
}
#endif