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


@module.register_simple("list->tuple")
def list_to_tuple(stack: T[V, S], fail: Fail):
    head, rest = stack
    if head.tag != "vec":
        fail(f"{head} must be a list")
    el = head.values
    values = []
    while len(el) != 0:
        if len(el) != 2:
            fail('a list must be composed of 2 long tuples')
        car, cdr = el
        if cdr.tag != 'vec':
            fail('a list must only contain tuples as the second element')
        values.append(car)
        el = cdr.values

    return Vec(values), rest