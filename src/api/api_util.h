#pragma once

#if defined(_MSC_VER)
  #define BNG_API_EXPORT __declspec(dllexport)
  #define BNG_API_IMPORT __declspec(dllimport)
#else
  #define BNG_API_EXPORT __attribute__((visibility("default")))
  #define BNG_API_IMPORT
#endif
