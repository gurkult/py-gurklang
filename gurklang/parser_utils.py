from dataclasses import dataclass
import re
from dataclasses import dataclass
from typing import Collection, Generic, Iterable, Iterator, Pattern, TypeVar


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

    @property
    def token_type(self) -> type[Token[TokenName]]:
        return Token

    def tokenize(self, source: str) -> Iterator[Token[TokenName]]:
        for match in self.pattern.finditer(source):
            name, value = next(
                (name, value) for (name, value) in match.groupdict().items()
                if value is not None
            )
            if name not in self.ignore:
                yield Token(name, value, match.start())  # type: ignore


def build_regexp_source(lookup: Iterable[tuple[str, str]]):
    return "|".join(f"(?P<{name}>{pattern})" for name, pattern in lookup)  # type:ignore


def build_regexp(lookup: Iterable[tuple[str, str]], flags: re.RegexFlag = re.RegexFlag(0)):
    return re.compile(build_regexp_source(lookup), flags)


def build_tokenizer(
    normal_tokens: tuple[tuple[TokenName, str], ...],
    flags: re.RegexFlag = re.RegexFlag(0),
    *,
    ignored_tokens: tuple[tuple[str, str], ...],
) -> Tokenizer[TokenName]:
    return Tokenizer(
        build_regexp(normal_tokens + ignored_tokens, flags),
        ignore=[name for name, _pattern in ignored_tokens]
    ) # type: ignore
