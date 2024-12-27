#pragma once

#if defined(_MSC_VER)
# define API_EXPORT __declspec(dllexport)
# define API_IMPORT __declspec(dllimport)
#else
# define API_EXPORT __attribute__((visibility("default")))
# define API_IMPORT
#endif
