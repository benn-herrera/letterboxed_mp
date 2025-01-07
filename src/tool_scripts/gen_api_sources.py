#!/usr/bin/env python3
import sys
from typing import Optional

import cyclopts
import json
from pathlib import Path

gen_api_version = "0.5.0"

PROJECT_DIR = Path(sys.argv[0]).parent.parent.parent.absolute()
CPP_SRC_DIR = PROJECT_DIR / "src"
CPP_PLATFORM_DIR = CPP_SRC_DIR / "platform"
KOTLIN_SRC_DIR = PROJECT_DIR / "kotlin_project"
SWIFT_SRC_DIR = PROJECT_DIR / "swift_project"
JS_SRC_DIR = PROJECT_DIR / "wasm_project"

app = cyclopts.App(
    version=gen_api_version,
    name=f"${Path(sys.argv[0]).name}"
)

def _is_public_data_member(obj, field: str, value) -> bool:
    return (not field.startswith("_")) and (not callable(value))

def _init_obj_from_dict(obj, dct: dict):
    dct_keys = set(dct.keys())
    unset_attrs = set()
    for field in [field for (field, value) in obj.__dict__.items() if _is_public_data_member(obj, field, value)]:
        if field in dct:
            setattr(obj, field, dct.get(field))
            dct_keys.remove(field)
        elif (not hasattr(obj, "is_attr_optional")) or (not obj.is_attr_optional(field)):
            unset_attrs.add(field)
    if dct_keys:
        raise ValueError(f"{dct_keys} not handled")
    if unset_attrs:
        raise ValueError(f"{unset_attrs} are required but were not set")

_base_types = [
    "bool",
    "int8",
    "uint8",
    "int16",
    "uint16",
    "int32",
    "uint32",
    "int64",
    "uint64",
    "intptr",
    "float32",
    "float64",
    "String",
    "ConstString"
]

class Named:
    def __init__(self, name: Optional[str]=None):
        self.name: Optional[str] = name

    def __str__(self):
        return f"{self.name}{{{self.__class__.__name__}}}"

class BaseType(Named):
    def __init__(self, name):
        super().__init__(name)
        self.type = name

_type_table = {name: BaseType(name) for name in _base_types}

def _add_type(name: str, obj):
    if name in _type_table:
        raise ValueError(f"{name} already defined as {_type_table[name]}, can't redefine as {obj}")
    _type_table[name] = obj

def _get_type(name: str):
    if name not in _type_table:
        raise ValueError(f"type {name} is not in the type table")
    return _type_table[name]

def _get_base_type(name: str) -> BaseType:
    t: BaseType = _get_type(name)
    if not isinstance(t, BaseType):
        raise ValueError(f"{name} ({t}) is not a base type")
    return t


class Typed(Named):
    def __init__(self, *, can_be_void: bool = False):
        self.type: Optional[str] = None
        self._can_be_void = can_be_void
        super().__init__()

    @property
    def type_obj(self):
        if self._can_be_void and self.type == "void":
            return None
        return _get_type(self.type)

    def __str__(self):
        return f"{self.name}: {self.type_obj}"


class ConstantDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.value = None
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            if not ("int" in self.type or "float" in self.type):
                raise ValueError(f"{self} type must be numerical.")


class EnumValue(Named):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.value = None
        if dct:
            _init_obj_from_dict(self, dct)


class EnumDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        if dct:
            _init_obj_from_dict(self, dct)
            self.members = [EnumValue(m) for m in self.members]
            _add_type(self.name, self)
            _get_base_type(self.type)
            if "int" not in self.type:
                raise ValueError(f"{self.type_obj} is not an integer type")


class OpaqueDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self.name, self)
            _ = self.type_obj
            if "int" not in self.type:
                raise ValueError(f"{self.type_obj} is not an integer type")


class MemberDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.array_count = None
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj

    def is_attr_optional(self, attr_name: str) -> bool:
        if not hasattr(self, attr_name):
            raise ValueError(f"{attr_name} is not an attribute of {self} ")
        return attr_name in ["array_count"]


class StructDef(Named):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self.name, self)
            self.members = [MemberDef(m) for m in self.members]


class ParameterDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj


class FunctionDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__(can_be_void=True)
        self.parameters = []
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            self.parameters = [ParameterDef(p) for p in self.parameters]


class ApiDef:
    def __init__(self, dct: Optional[dict] = None):
        self.version: Optional[str] = None
        self.constants = []
        self.enums = []
        self.opaques = []
        self.structs = []
        self.functions = []
        if dct:
            _init_obj_from_dict(self, dct)
            self.constants = [ConstantDef(c) for c in self.constants]
            self.enums = [EnumDef(e) for e in self.enums]
            self.opaques = [OpaqueDef(o) for o in self.opaques]
            self.structs = [StructDef(s) for s in self.structs]
            self.functions = [FunctionDef(f) for f in self.functions]


@app.default
def generate(
        api_def: Path = CPP_SRC_DIR / "api/api_def.json",
        c_dir: Path = CPP_SRC_DIR / "api",
        cpp_dir: Path = CPP_SRC_DIR / "engine",
        wasm_binding_dir: Path = CPP_PLATFORM_DIR / "wasm",
        js_dir = JS_SRC_DIR / "modules",
        jni_binding_dir: Path = CPP_PLATFORM_DIR / "mobile/android",
        kotlin_dir: Path = KOTLIN_SRC_DIR / "lbsolverlib/src/main/kotlin/com/tinybitsinteractive/lbsolverlib/nativecore",
        swift_binding_dir: Path = CPP_PLATFORM_DIR / "mobile/ios",
        swift_dir: Path = SWIFT_SRC_DIR / "lbsolverlib/Sources/lbsolverlib"
):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        path to .json file with API definition
    c_dir
        directory for generated pure c
    cpp_dir
        directory for generated c++
    wasm_binding_dir
        directory for generated wasm binding code
    js_dir
        directory for generated javascript
    jni_binding_dir
        directory for generated jni bindings
    kotlin_dir
        directory for generated kotlin
    swift_binding_dir
        directory for generated swift bindings
    swift_dir
        directory for generated swift
    """

    api_def = ApiDef(json.loads(api_def.read_text(encoding="utf8")))

if __name__ == "__main__":
    app()
