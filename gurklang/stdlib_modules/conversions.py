from functools import reduce
from ..builtin_utils import BuiltinModule, Fail
from ..types import Tuple, Value, Stack, Vec


module = BuiltinModule("conversions")
T, V, S = Tuple, Value, Stack


@module.register_simple("tuple->list")
def tuple_to_list(stack: T[V, S], fail: Fail):
    head, rest = stack
    if head.tag != "vec":
        fail(f"{head} must be a tuple")
    nested = reduce(lambda a, b: Vec([b, a]), reversed(head.values), Vec([]))
    return nested, rest