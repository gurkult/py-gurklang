from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Generic, Iterator, Mapping, NewType, Optional,  Tuple, TypeVar, Union, overload


V = TypeVar("V")
T = TypeVar("T")


NotFoundT = NewType("NotFoundT", object)
NotFound = NotFoundT(object())


@dataclass
class TrieLeaf(Generic[V]):
    value: V

    def search(self, prefix: str) -> Union[V, NotFoundT]:
        if prefix == "":
            return self.value
        else:
            return NotFound

    def search_all(self, prefix: str) -> Iterator[Tuple[str, V]]:
        if prefix == "":
            yield ("", self.value)


@dataclass
class TrieNode(Generic[V]):
    variants: Dict[str, TrieElement[V]]

    def set(self, prefix: str, value: V):
        if prefix[:1] in self.variants:
            v = self.variants[prefix[:1]]
            if isinstance(v, TrieLeaf):
                v.value = value
            else:
                v.set(prefix[1:], value)
        elif prefix == "":
            self.variants[""] = TrieLeaf(value)
        else:
            node: TrieNode[V] = TrieNode({})
            node.set(prefix[1:], value)
            self.variants[prefix[0]] = node

    def search(self, prefix: str) -> Union[V, NotFoundT]:
        if prefix[:1] in self.variants:
            return self.variants[prefix[:1]].search(prefix[1:])
        else:
            return NotFound

    def search_all(self, prefix: str) -> Iterator[Tuple[str, V]]:
        if prefix == "":
            for (k, variant) in self.variants.items():
                for subk, value in variant.search_all(prefix[1:]):
                    yield (k + subk, value)
        elif prefix[0] in self.variants:
            for (subk, value) in self.variants[prefix[0]].search_all(prefix[1:]):
                yield (prefix[0] + subk, value)


TrieElement = Union[TrieLeaf[V], TrieNode[V]]


@dataclass(init=False)
class Trie(Generic[V]):
    node: TrieNode[V]

    def __init__(self, mapping: Optional[Mapping[str, V]] = None):
        self.node = TrieNode({})  # type: ignore
        if mapping is not None:
            for k, v in mapping.items():
                self[k] = v

    @overload
    def get(self, key: str) -> Optional[V]: ...
    @overload
    def get(self, key: str, default: T) -> Union[V, T]: ...

    def get(self, key, default):
        result = self.node.search(key)
        if result is NotFound:
            return default
        else:
            return result

    def __setitem__(self, key: str, value: V):
        self.node.set(key, value)

    def __getitem__(self, key: str) -> V:
        result = self.node.search(key)
        if result is NotFound:
            raise KeyError(key)
        else:
            return result  # type: ignore

    def __contains__(self, key: str):
        return self.node.search(key) is not NotFound

    def __repr__(self):
        return "Trie(" + repr(dict(self.prefix_search(""))) + ")"

    def prefix_search(self, prefix: str) -> Iterator[Tuple[str, V]]:
        yield from self.node.search_all(prefix)
