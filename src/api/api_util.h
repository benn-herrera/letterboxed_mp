#pragma once

#if defined(_MSC_VER)
  #define BNG_API_EXPORT __declspec(dllexport)
  #define BNG_API_IMPORT __declspec(dllimport)
#else
  #define BNG_API_EXPORT __attribute__((visibility("default")))
  #define BNG_API_IMPORT
#endif

#if defined(BNG_IS_WASM)
  #include <string>
  #define BNG_API_STRING std::string
  #define BNG_API_STRUCT_REF(STYPE) STYPE&
  #define BNG_API_DEREF_STRUCT(SINST) SINST
  #define bng_make_api_string(STR) STR
#else
  // contract: returned memory buffer ownership passes to caller.
  //           must release with free()
  #define BNG_API_STRING char*
  #define BNG_API_STRUCT_REF(STYPE) STYPE*
  #define BNG_API_DEREF_STRUCT(SINST) (*SINST)
  #define bng_make_api_string(STR) strdup(STR)
#endif
