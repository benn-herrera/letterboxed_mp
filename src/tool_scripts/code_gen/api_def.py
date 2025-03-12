from enum import StrEnum
from typing import Optional, Set, List, Dict
import json
from pathlib import Path


def snake_to_camel(val: str, *, capitalize=False) -> str:
    return "".join(
        [(s.capitalize() if (capitalize or i > 0) else s) for (i, s) in enumerate(val.split("_"))]
    )


class RefType(StrEnum):
    raw = "*"
    non_optional = "&"
    shared = "shared"
    unique = "unique"


class Base:
    def __init__(self, **kwargs):
        dct_keys = set(kwargs.keys())
        unset_attrs = set()
        for field in [
            field
            for (field, value) in self.__dict__.items()
            if Base._is_public_data_member(self, field, value)
        ]:
            if field in kwargs:
                setattr(self, field, kwargs.get(field))
                dct_keys.remove(field)
            else:
                if self._is_attr_optional(field):
                    continue
                unset_attrs.add(field)
        err_msgs = []
        if dct_keys:
            err_msgs.append(
                f"{dct_keys} are not attributes of {self.__class__.__name__} {getattr(self, 'name', '')}"
            )
        if unset_attrs:
            err_msgs.append(
                f"{unset_attrs} are required attributes of {self.__class__.__name__} {getattr(self, 'name', '')} but were not set"
            )
        if err_msgs:
            raise ValueError("\n".join(err_msgs))
        self._validate()

    def _is_attr_optional(self, attr_name: str) -> bool:
        return False

    def _validate(self):
        pass

    @staticmethod
    def _is_public_data_member(obj, field: str, value) -> bool:
        return (not field.startswith("_")) and (not callable(value))


class Named(Base):
    def __init__(self, **kwargs):
        self.name: Optional[str] = None
        super().__init__(**kwargs)

    def __str__(self):
        return f"{self.name}{{{self.__class__.__name__}}}"


class BaseType(Named):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _add_type(self)

    def __str__(self):
        return f"{self.__class__.__name__} {self.name}"

    @property
    def is_int(self) -> bool:
        return False

    @property
    def is_bool(self) -> bool:
        return False

    @property
    def is_float(self) -> bool:
        return False

    @property
    def is_primitive(self) -> bool:
        return False

    @property
    def is_number(self) -> bool:
        return self.is_int or self.is_float

    @property
    def is_number_or_bool(self) -> bool:
        return self.is_number or self.is_bool

    @property
    def is_void(self) -> bool:
        return False

    @property
    def is_string(self) -> bool:
        return False

    @property
    def type_obj(self) -> "BaseType":
        return self

    @property
    def resolved_type_obj(self) -> "BaseType":
        return self


class PrimitiveType(BaseType):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def is_int(self) -> bool:
        return "int" in self.name

    @property
    def is_float(self) -> bool:
        return "float" in self.name

    @property
    def is_void(self) -> bool:
        return self.name == "void"

    @property
    def is_string(self) -> bool:
        return self.name == "string"

    @property
    def is_bool(self) -> bool:
        return self.name == "bool"

    @property
    def is_primitive(self) -> bool:
        return True


class TypedNamed(Named):
    def __init__(self, **kwargs):
        self.type: Optional[str] = None
        self.ref_type = None
        self.array_count: Optional[int] = None
        self.is_list = False
        self.is_const = False
        super().__init__(**kwargs)
        if self.ref_type:
            self.ref_type = RefType[self.ref_type]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in [
            "ref_type",
            "is_list",
            "is_const",
            "array_count",
        ] or super()._is_attr_optional(attr_name)

    def _validate(self):
        if self.is_list and self.is_array:
            raise ValueError(f"{self} - array_count and is_list are mutually exclusive")
        if self.resolved_type_obj.is_void and (self.is_list or self.is_array or self.is_const):
            raise ValueError(f"{self} - void type can't be const, array, or list")

    def __str__(self):
        if self.is_array:
            mods = f"[{self.array_count}]"
        elif self.is_list:
            mods = "[list]"
        elif self.ref_type is not None:
            mods = f"({self.ref_type.name}_ref)"
        else:
            mods = ""
        return f"{self.__class__.__name__} {self.name}: {self.type_obj}{mods}"

    @property
    def is_array(self):
        return self.array_count is not None

    @property
    def type_obj(self) -> BaseType:
        return get_type(self.type)

    @property
    def resolved_type_obj(self) -> BaseType:
        return self.type_obj.resolved_type_obj

    @property
    def is_int(self) -> bool:
        return self.resolved_type_obj.is_int

    @property
    def is_float(self) -> bool:
        return self.resolved_type_obj.is_float

    @property
    def is_number(self) -> bool:
        return self.resolved_type_obj.is_number

    @property
    def is_primitive(self) -> bool:
        return self.resolved_type_obj.is_primitive

    @property
    def is_number_or_bool(self) -> bool:
        return self.resolved_type_obj.is_number_or_bool

    @property
    def is_void(self) -> bool:
        return self.resolved_type_obj.is_void

    @property
    def is_string(self) -> bool:
        return self.resolved_type_obj.is_string

    @property
    def is_bool(self) -> bool:
        return self.resolved_type_obj.is_bool


class ConstantDef(TypedNamed):
    def __init__(self, **kwargs):
        self.value = None
        super().__init__(**kwargs)

    def _validate(self):
        super()._validate()
        if (self.ref_type or self.is_list or self.is_array) or not self.is_number:
            raise ValueError(f"{self} type {self} is not a simple numeric type.")
        if self.is_int and self.has_float_value:
            raise ValueError(f"{self} assigns a float value to an int type")

    def __str__(self):
        return f"{super().__str__()} = {self.value}"

    @property
    def has_float_value(self) -> bool:
        return "." in f"{self.value}"


class EnumValue(ConstantDef):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class EnumDef(BaseType):
    def __init__(self, **kwargs):
        self.members = []
        self.base_type = "int32"
        super().__init__(**kwargs)
        self.members = [EnumValue(**m, type=self.name) for m in self.members]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["base_type"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        rbt = self.resolved_base_type_obj
        if not rbt.is_int:
            raise ValueError(f"{self} is not integral.")

    def __str__(self):
        return super().__str__() + f"({self.base_type})"

    @property
    def base_type_obj(self) -> BaseType:
        return get_type(self.base_type)

    @property
    def resolved_base_type_obj(self) -> BaseType:
        return self.base_type_obj.resolved_type_obj

    @property
    def is_int(self) -> bool:
        return True


class AliasDef(BaseType):
    def __init__(self, **kwargs):
        self.base_type: Optional[str] = None
        self.ref_type: Optional[RefType] = None
        self.array_count: Optional[int] = None
        self.is_list = False
        self.is_const = False
        super().__init__(**kwargs)

    @property
    def is_array(self):
        return self.array_count is not None

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["ref_type"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.resolved_type_obj.is_void:
            raise ValueError(f"{self} - can't alias void type")

    @property
    def base_type_obj(self) -> BaseType:
        return get_type(self.base_type)

    @property
    def resolved_type_obj(self):
        bt = self.base_type_obj
        while isinstance(bt, AliasDef):
            bt = self.base_type_obj
        return bt


class MemberDef(TypedNamed):
    def __init__(self, **kwargs):
        self.is_static = False
        super().__init__(**kwargs)

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_static"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.resolved_type_obj.is_void:
            raise ValueError(f"{self} can't have a void type")


class StructDef(BaseType):
    def __init__(self, **kwargs):
        self.members = []
        super().__init__(**kwargs)
        self.members = [MemberDef(**m) for m in self.members]


class ParameterDef(TypedNamed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_list"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.is_array:
            raise ValueError(f"{self} - can't pass arrays as parameters")


class FunctionDef(TypedNamed):
    def __init__(self, **kwargs):
        self.parameters = []
        self.is_factory = False
        super().__init__(**kwargs)
        self.parameters = [ParameterDef(**p) for p in self.parameters]
        if self.is_factory:
            self.is_const = False
            if self.ref_type is None:
                self.ref_type = RefType.raw

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["parameters", "is_factory"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.is_factory and self.ref_type == RefType.non_optional:
            raise ValueError(f"{self} is a factory - ref_type must be 'raw', 'shared', or 'unique'")


class MethodDef(TypedNamed):
    def __init__(self, **kwargs):
        self.parameters = []
        self.is_static = False
        self.is_const_method = False
        self.is_factory = False
        super().__init__(**kwargs)
        self.parameters = [ParameterDef(**p) for p in self.parameters]
        if self.is_factory:
            self.is_const = False
            if self.ref_type is None:
                self.ref_type = RefType.raw

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in [
            "parameters",
            "is_static",
            "is_const_method",
            "is_factory",
        ] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.is_static and self.is_const_method:
            raise ValueError(f"{self} can't be both static and const method")
        if self.is_factory and self.ref_type == RefType.non_optional:
            raise ValueError(f"{self} is a factory - ref_type must be 'raw', 'shared', or 'unique'")


class ClassDef(BaseType):
    def __init__(self, **kwargs):
        self.constants = []
        self.members = []
        self.methods = []
        super().__init__(**kwargs)
        self.constants = [ConstantDef(**c) for c in self.constants]
        self.members = [MemberDef(**m) for m in self.members]
        self.methods = [MethodDef(**m) for m in self.methods]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["constants", "methods", "members"] or super()._is_attr_optional(
            attr_name
        )

    @property
    def static_factory(self) -> Optional[MethodDef]:
        return next((m for m in self.methods if m.is_factory and m.resolved_type_obj is self), None)


class ApiDef(Named):
    def __init__(self, **kwargs):
        self.version: Optional[str] = None
        self.aliases = []
        self.classes = []
        self.constants = []
        self.enums = []
        self.functions = []
        self.structs = []
        super().__init__(**kwargs)

        init_type_table()
        self.constants = [ConstantDef(**c) for c in self.constants]
        self.enums = [EnumDef(**e) for e in self.enums]
        self.aliases = [AliasDef(**o) for o in self.aliases]
        self.structs = [StructDef(**s) for s in self.structs]
        self.classes = [ClassDef(**s) for s in self.classes]
        self.functions = [FunctionDef(**f) for f in self.functions]
        self._types_used_in_list = None
        self._type_array_counts = None

    @staticmethod
    def from_file(json_path: Path):
        return ApiDef(**json.loads(json_path.read_text(encoding="utf8")))

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in [
            "aliases",
            "classes",
            "constants",
            "enums",
            "functions",
            "structs",
        ] or super()._is_attr_optional(attr_name)

    def _validate(self):
        if not (
            self.constants
            or self.enums
            or self.aliases
            or self.structs
            or self.classes
            or self.functions
        ):
            raise ValueError(f"{self} defines no api")

    @property
    def types_used_in_list(self) -> Set[BaseType]:
        if self._types_used_in_list is None:
            self._collate_array_list_usage()
        return self._types_used_in_list

    @property
    def type_array_counts(self) -> Dict[BaseType, List[int]]:
        if self._type_array_counts is None:
            self._collate_array_list_usage()
        return self._type_array_counts

    def _collate_array_list_usage(self):
        used_in_list = set()
        type_array_counts = {}

        def register_usage(usage):
            if usage.is_list:
                used_in_list.add(usage.resolved_type_obj)
            if usage.is_array:
                type_array_counts.setdefault(usage.resolved_type_obj, []).append(usage.array_count)

        def register_usages(usages):
            for usage in usages:
                register_usage(usage)

        register_usages(self.constants)

        for sd in self.structs:
            register_usages(sd.members)
        for cd in self.classes:
            register_usages(cd.members)
            register_usages(cd.methods)
            for md in cd.methods:
                register_usages(md.parameters)
        for fd in self.functions:
            register_usages(fd.parameters)

        self._types_used_in_list = used_in_list
        self._type_array_counts = type_array_counts


_type_table = {}


def reset_type_table():
    global _type_table
    _type_table = {}


def get_type(name: str) -> BaseType:
    if name not in _type_table:
        raise ValueError(f"type {name} is not in the type table")
    t = _type_table[name]
    return t


def _add_type(typ: BaseType):
    if not isinstance(typ, BaseType):
        raise ValueError(f"{typ} is not a type.")
    if typ.name in _type_table:
        raise ValueError(
            f"{typ.name} already defined as {_type_table[typ.name]}, can't redefine as {typ}"
        )
    _type_table[typ.name] = typ


def init_type_table():
    reset_type_table()
    base_types = [
        "void",
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
        "string",
    ]
    for base_type in base_types:
        PrimitiveType(name=base_type)
