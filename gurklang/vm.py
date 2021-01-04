import weakref
from immutables import Map
from typing import Callable, Optional, Sequence, Tuple, Union

from . import prelude
from gurklang.types import (
    CallByValue, CodeFlags, MakeScope, NativeFunction, PopScope, Put,
    Scope, Stack, Instruction, Code, State, Vec
)
from collections import defaultdict, deque
import threading


MiddlewareT = Callable[[Instruction, Stack, Stack], None]


_SCOPE_ID_LOCK = threading.Lock()
_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    with _SCOPE_ID_LOCK:
        _SCOPE_ID += 1
    return _SCOPE_ID


def make_scope(parent: Optional[int]) -> Scope:
    return Scope(parent, generate_scope_id(), Map())


def _load_function(pipe: "deque[Instruction]", function: Union[Code, NativeFunction]):
    if function.tag == "native":
        pipe.append(CallByValue())
        pipe.append(Put(function))
    elif function.flags & CodeFlags.PARENT_SCOPE or function.closure is None:
        pipe.extend(reversed(function.instructions))
    else:
        pipe.append(PopScope())
        pipe.extend(reversed(function.instructions))
        pipe.append(MakeScope(function.closure))


def call(state: State, function: Union[Code, NativeFunction]) -> State:
    """
    Stackless implementation of calling a function.

    Instructions are piped into a deque, from which they're popped
    and executed one by one.
    """
    return call_with_middleware(state, function, lambda _, __, ___: None)


def call_with_middleware(
    state: State,
    function: Union[Code, NativeFunction],
    middleware: MiddlewareT,
) -> State:
    """
    Like `call`, but execute some action on each change
    """
    pipe: "deque[Instruction]" = deque()

    _load_function(pipe, function)

    refcount = defaultdict(int, {builtin_scope.id: 1, global_scope.id: 1})

    def finalizer(scope_id: int):
        future_callbacks.append((3, lambda: _real_finalizer(scope_id)))

    def _real_finalizer(scope_id: int):
        nonlocal state
        if scope_id in (builtin_scope.id, global_scope.id):
            return
        refcount[scope_id] -= 1
        scope = state.get_scope(scope_id)
        if scope.persistent:
            return
        parent_id = scope.parent
        if parent_id is not None:
            _real_finalizer(parent_id)
        if refcount[scope_id] < 0:
            pass
        if refcount[scope_id] == 0:
            state = state.kill_scope(scope_id)
            del refcount[scope_id]


    def introducer(scope_id: int):
        nonlocal state
        if scope_id in (builtin_scope.id, global_scope.id):
            return
        refcount[scope_id] += 1
        scope = state.get_scope(scope_id)
        if scope.persistent:
            return
        parent_id = scope.parent
        if parent_id is not None:
            introducer(parent_id)

    future_callbacks = []

    while pipe:
        new_future_callbacks = []
        for (i, cb) in future_callbacks[:]:
            if i <= 0:
                cb()
            else:
                new_future_callbacks.append((i-1, cb))
        future_callbacks = new_future_callbacks

        instruction = pipe.pop()

        old_state = state

        if instruction.tag == "call":
            pipe.append(CallByValue())
            pipe.append(Put(state.look_up_name_in_current_scope(instruction.function_name)))

        elif instruction.tag == "call_by_value":
            (function, stack) = state.stack  # type: ignore
            state = state.with_stack(stack)
            if function.tag == "code":
                _load_function(pipe, function)
            else:
                try:
                    state = function.fn(state)
                except:
                    print(f"{function=}")
                    raise

        else:
            state, to_introduce, to_finalize = execute(state, instruction, introducer, finalizer)
            for id in to_introduce:
                introducer(id)
            for id in to_finalize:
                finalizer(id)

        middleware(instruction, old_state.stack, state.stack)

    for (_, cb) in future_callbacks:
        cb()
    return state


ClosureCallback = Callable[[int], None]

def execute(
    state: State,
    instruction: Instruction,
    introducer: ClosureCallback,
    finalizer: ClosureCallback
) -> Tuple[State, Tuple[int, ...], Tuple[int, ...]]:
    """
    Execute an instruction and return new state of the system.
    """
    if instruction.tag == "put":
        return state.push(instruction.value), (), ()

    elif instruction.tag == "put_code":
        return state.push(
            Code(
                instructions=instruction.instructions,
                closure=state.current_scope_id,
                source_code=instruction.source_code,
                introducer=weakref.ref(introducer),
                finalizer=weakref.ref(finalizer),
            ),
        ), (state.current_scope_id,), ()

    elif instruction.tag == "make_vec":
        stack = state.stack
        elements = []
        for _ in range(instruction.size):
            head, stack = stack  # type: ignore
            elements.append(head)
        return state.with_stack(stack).push(Vec(elements[::-1])), (), ()

    elif instruction.tag == "make_scope":
        new_id = generate_scope_id()
        return state.make_scope(instruction.parent_id, new_id), (instruction.parent_id, new_id,), ()

    elif instruction.tag == "pop_scope":
        return state.pop_scope(), (), (state.current_scope_id,)

    else:
        raise RuntimeError(instruction)


builtin_scope = prelude.module.make_scope(generate_scope_id())
global_scope = make_scope(parent=builtin_scope.id)


def run(instructions: Sequence[Instruction]):
    return run_with_middleware(instructions, middleware = lambda _, __, ___: None)


def run_with_middleware(instructions: Sequence[Instruction], middleware: MiddlewareT):
    return call_with_middleware(
        State.make(global_scope, builtin_scope),
        Code(instructions, closure=None, name="<entry-point>", flags=CodeFlags.PARENT_SCOPE),
        middleware
    )
