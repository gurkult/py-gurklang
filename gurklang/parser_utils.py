import re
from typing import Iterable

def build_regexp_source(lookup: Iterable[tuple[str, str]]):
    return "|".join(f"(?P<{name}>{pattern})" for name, pattern in lookup)

def build_regexp(lookup: Iterable[tuple[str, str]], flags: re.RegexFlag = re.RegexFlag(0)):
    return re.compile(build_regexp_source(lookup), flags)