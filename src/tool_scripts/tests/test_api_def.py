import sys
from pathlib import Path
from _pytest.fixtures import fixture

TESTS_DIR = Path(__file__).parent
TOOLS_DIR = TESTS_DIR.parent
CODE_GEN_DIR = TOOLS_DIR / "code_gen"
OUT_DIR = TESTS_DIR / "test_output"

sys.path.append(TOOLS_DIR.as_posix())
sys.path.append(CODE_GEN_DIR.as_posix())

# noinspection PyUnresolvedReferences
from api_def import (
    Named,
    TypedNamed,
    BaseType,
    ApiDef,
    init_type_table,
    reset_type_table,
    get_type,
)

#
# fixtures
#

@fixture
def api_no_api() -> dict:
    return dict(
        name="test_api",
        version="1.2.3"
    )

@fixture
def api_minimal_valid() -> dict:
    return dict(
        name="test_api",
        version="1.2.3",
        constants=[
            dict(
                type="int32",
                name="the_const",
                value="1"
            )
        ]
    )

#
# tests
#

def test_correct_usage():
    n = Named(name="norman")
    assert n.name == "norman"

def test_required_attr():
    try:
        Named()
    except ValueError as ve:
        return
    # should have thrown because name="foo" missing
    assert False

def test_unhandled_attr():
    try:
        Named(name="foo", unhandled="bar")
    except ValueError as ve:
        return
    # should have thrown because unhandled is not a valid attribute
    assert False

def test_type_registration():
    reset_type_table()
    bt = BaseType(name="the_type_name")
    assert bt is get_type(bt.name)

    reset_type_table()
    try:
        get_type(bt.name)
    except ValueError as ve:
        return
    # type should not be in table
    assert False

def test_init_primitive_types():
    init_type_table()
    get_type("int32")
    get_type("bool")
    get_type("string")
    get_type("float64")
    reset_type_table()

def test_optional_attr():
    # is_const optional - specified
    reset_type_table()
    BaseType(name="the_type_name")
    tn = TypedNamed(name="the_var_name", type="the_type_name", is_const=True)
    assert tn.name == "the_var_name" and tn.type == "the_type_name" and tn.is_const == True
    # is_const not specified. should be fine.
    tn = TypedNamed(name="the_var_name", type="the_type_name")
    assert tn.name == "the_var_name" and tn.type == "the_type_name" and tn.is_const == False

def test_validation():
    reset_type_table()
    BaseType(name="the_type_name")
    try:
        TypedNamed(name="the_var_name", type="the_type_name", is_list=True, is_array=True)
    except ValueError as ve:
        return
    # is_list and is_array should fail validation as mutually exclusive
    assert False

def test_api_no_api(api_no_api: dict):
    try:
        ApiDef(**api_no_api)
    except ValueError as ve:
        return
    # should throw when no api guts are defined
    assert False

def test_api_minimal_valid(api_minimal_valid: dict):
    api = ApiDef(**api_minimal_valid)
    assert api.name == "test_api"
    assert api.version == "1.2.3"

def test_assign_float_to_int():
    try:
        ApiDef(
            name="test_api",
            version="1.2.3",
            constants=[
                dict(
                    type="int32",
                    name="the_const",
                    value=1.5
                )
            ]
        )
    except ValueError as ve:
        return
    # should have thrown for assigning 1.5 to int value
    assert False
