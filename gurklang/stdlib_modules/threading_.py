from typing import List, Optional, TypeVar, Tuple, Deque

from immutables import Map
from ..vm_utils import render_value_as_source, stringify_value
from ..builtin_utils import BuiltinModule, Fail, make_simple, vec_to_stack, stack_to_vec
from ..types import Atom, CallByValue, Code, CodeFlags, Instruction, Put, State, Value, Stack, Scope, Vec
from queue import Queue
import heapq
import gurklang.vm
import threading


module = BuiltinModule("threading")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


ThreadQ = Queue[Tuple[int, Stack]]


def _run_function(
    n: int,
    queue: ThreadQ,
    stack: Stack,
    instructions: List[Instruction],
    name: str,
    source_code: Optional[str]
):
    begin_state = State.make(gurklang.vm.global_scope, gurklang.vm.builtin_scope).with_stack(stack)
    end_state = gurklang.vm.call(
        begin_state,
        Code(instructions, None, name=name, source_code=source_code)
    )
    queue.put((n, end_state.stack))


@module.register()
def run_concurrently(state: State, fail: Fail):
    """
    Launch a new interpreter and run a function in it

    (functions intial-stacks -- resulting-stacks)
    """
    (stack_vec, (fnvec, rest)) = state.infinite_stack()
    stacks = [vec_to_stack(sv, fail) for sv in stack_vec.values]  # type: ignore

    result_queue: ThreadQ = Queue()
    threads: List[threading.Thread] = []
    for i, (stack, fn) in enumerate(zip(stacks, fnvec.values)):  # type: ignore
        thread = threading.Thread(
            name=f"My Thread {i}",
            target=_run_function,
            args=(i, result_queue, stack, list(fn.instructions), fn.name, fn.source_code)  # type: ignore
        )
        thread.start()
        threads.append(thread)

    results: List[Stack] = [None] * len(threads)  # type: ignore
    for _ in threads:
        i, stack = result_queue.get()
        results[i] = stack

    for thread in threads:
        thread.join()

    return (
        state
        .with_stack(rest)
        .push(Vec([stack_to_vec(stack) for stack in results]))
    )
