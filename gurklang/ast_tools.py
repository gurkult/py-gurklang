from typing import Iterator, NamedTuple, Tuple
from gurklang.stdlib_modules import modules
from gurklang.ast_parser import AtomLiteral, CodeLiteral, NameCall, VecLiteral
from gurklang.ast_parser import *
from gurklang.prelude import module as prelude_module

find_star_imports = find(t_atom, eq(AtomLiteral("all")), eq(NameCall("import")))
find_prefix_imports = find(t_atom, eq(AtomLiteral("prefix")), eq(NameCall("import")))
find_list_imports = find(t_atom, avec(t_atom), eq(NameCall("import")))


def get_module(name: str):
    for module in modules:
        if module.name == name:
            return module
    return None


class Import(NamedTuple):
    module_name: str
    original_name: str
    imported_name: str


def find_imports(ast: CodeLiteral, include_prelude: bool = False) -> Iterator[Import]:
    if include_prelude:
        for name in prelude_module.members.keys():
            yield Import("prelude", name, name)

    for module_name, _all, _import in find_star_imports(ast.nodes):
        assert isinstance(module_name, AtomLiteral)
        m = get_module(module_name.value)
        if m is None:
            continue
        for name in m.members.keys():
            yield Import(module_name.value, name, name)

    for module_name, _prefix, _import in find_prefix_imports(ast.nodes):
        assert isinstance(module_name, AtomLiteral)
        m = get_module(module_name.value)
        if m is None:
            continue
        for name in m.members.keys():
            yield Import(module_name.value, name, f"{module_name.value}.{name}")

    for module_name, imported_names, _import in find_list_imports(ast.nodes):
        assert isinstance(module_name, AtomLiteral)
        assert isinstance(imported_names, VecLiteral)
        m = get_module(module_name.value)
        if m is None:
            continue
        for name in imported_names.nodes:
            if not isinstance(name, AtomLiteral):
                continue
            yield Import(module_name.value, name.value, name.value)
