from dataclasses import dataclass
import re
from dataclasses import dataclass
from typing import Callable, Collection, Generic, Iterable, Iterator, Optional, Pattern, TypeVar


TokenName = TypeVar("TokenName", bound=str)


@dataclass
class Token(Generic[TokenName]):
    name: TokenName
    value: str
    position: int


@dataclass
class Tokenizer(Generic[TokenName]):
    """
    Tokenizer with enhanced type safety.

    Don't instantiate this class directly, use `build_tokenizer` instead.
    """
    pattern: Pattern[str]
    ignore: Collection[str] = ()
    middleware: Callable[[TokenName, str], tuple[TokenName, str]] = lambda name, v: (name, v)

    @property
    def token_type(self) -> type[Token[TokenName]]:
        return Token

    def tokenize(self, source: str) -> Iterator[Token[TokenName]]:
        for match in self.pattern.finditer(source):
            name, value = next(
                (name, value) for (name, value) in match.groupdict().items()
                if value is not None
            )
            name, value = self.middleware(name, value)
            if name not in self.ignore:
                yield Token(name, value, match.start())  # type: ignore


def build_regexp_source(lookup: Iterable[tuple[str, str]]):
    return "|".join(f"(?P<{name}>{pattern})" for name, pattern in lookup)  # type:ignore


def build_regexp(lookup: Iterable[tuple[str, str]], flags: re.RegexFlag = re.RegexFlag(0)):
    return re.compile(build_regexp_source(lookup), flags)


def _make_middleware(lookup: dict[TokenName, Callable[[str], tuple[TokenName, str]]]):
    def middleware(name: TokenName, value: str):
        if name in lookup:
            return lookup[name](value)
        else:
            return (name, value)
    return middleware


def build_tokenizer(
    normal_tokens: tuple[tuple[TokenName, Optional[str]], ...],
    flags: re.RegexFlag = re.RegexFlag(0),
    *,
    ignored_tokens: tuple[tuple[str, str], ...] = (),
    middleware: dict[TokenName, Callable[[str], tuple[TokenName, str]]] = {},
) -> Tokenizer[TokenName]:
    return Tokenizer(
        build_regexp(tuple(filter(None, normal_tokens)) + ignored_tokens, flags),
        ignore=[name for name, _pattern in ignored_tokens],
        middleware=_make_middleware(middleware)
    ) # type: ignore
