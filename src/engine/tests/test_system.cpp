#include "systems/system.h"
#include "test_harness/test_harness.h"

using namespace bng::engine;

BNG_TEST(test_1, {
	System system;
	BT_CHECK(system.bar() == 2);
});

BNG_TEST(test_2, {
	System system;
	BT_CHECK(true);
	BT_CHECK(system.bar() != 1);
});
