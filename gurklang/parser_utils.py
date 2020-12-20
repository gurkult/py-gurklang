import re

def build_regexp_source(lookup: dict[str, str]):
    return "|".join(f"(?P<{name}>{pattern})" for name, pattern in lookup.items())

def build_regexp(lookup: dict[str, str], flags: re.RegexFlag = re.RegexFlag(0)):
    return re.compile(build_regexp_source(lookup), flags)