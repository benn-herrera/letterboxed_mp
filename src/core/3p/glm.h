#pragma once
#if defined(BNG_IS_MSVC)
# pragma warning(push, 0)
#else
# pragma clang diagnostic push
# pragma clang diagnostic ignored "-Weverything"
#endif

// TODO: set project-wide GLM options here.
#include "glm/glm.hpp"

#if defined(BNG_IS_MSVC)
# pragma warning(pop)
#else
# pragma clang diagnostic pop
#endif
