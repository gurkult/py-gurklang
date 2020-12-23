"""
Read Eval Print Loop

The essential interactive programming tool!
"""
from gurklang.vm_utils import render_value_as_source
import sys
import traceback
from typing import Any, Optional, Tuple

from colorama import init, Fore, Back
Fore: Any
Back: Any
init()

from .types import Code, CodeFlags, Scope, Stack
from .vm import run, call, make_scope
from .parser import parse, ParseError


def print_red(*xs):
    print(Fore.RED, end="")
    print(*xs, end="")
    print(Fore.RESET)


def _display_parse_error(e: ParseError):
    if e.is_eof:
        print_red("Unexpected EOF while parsing", e.while_parsing_what)
    else:
        print_red(
            f"Syntax error at {e.token.position} in token {e.token.value}"
            f" while parsing {e.while_parsing_what}"
        )


def _display_runtime_error(e: BaseException):
    print_red(type(e).__name__ + ": " + " ".join(e.args))
    print(Fore.YELLOW + "Type traceback? for complete Python traceback" + Fore.RESET)


def code(source: str) -> Code:
    parsed = parse(source)
    # PARENT_SCOPE is needed because otherwise, all of our names
    # (including imports) will vanish, as the scope will be popped
    return Code(parsed, name="<input>", closure=None, flags=CodeFlags.PARENT_SCOPE)


DEFAULT_PRELUDE = R"""
:repl-utils :all import
:inspect    :all import

">>> " :repl[prompt] var

"Gurklang v0.0.1" println
"---------------" println
"""


class Repl:
    stack: Stack
    scope: Scope
    last_traceback: Optional[Tuple[Any, Any, Any]]

    def __init__(self, prelude: str = DEFAULT_PRELUDE):
        stack, scope = run([])
        scope = make_scope(scope)  # we need to make our own scope not to change builtins
        stack, scope = call(stack, scope, code(prelude))
        self.stack = stack
        self.scope = scope
        self.last_traceback = None

    @property
    def prompt(self):
        (prompt_obj, _rest), _scope = call(self.stack, self.scope, code("repl[prompt]"))  # type: ignore
        if prompt_obj.tag != "str":
            raise RuntimeError(f"Expected string for `repl[prompt]`, got {prompt_obj}")
        return prompt_obj.value

    def _get_input(self):
        try:
            return input(Fore.CYAN + self.prompt + Fore.RESET)
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit!"

    def run(self):
        action = "continue"
        while action != "stop":
            command = self._get_input()
            action = self._process_command(command)

    def _process_command(self, command: str):
        return self._process_directives(command) or self._process_code(command)

    def _process_code(self, source_code: str):
        try:
            self.stack, self.scope = call(self.stack, self.scope, code(source_code))
        except ParseError as e:
            _display_parse_error(e)
        except KeyboardInterrupt as e:
            print_red("CTRL + C")
            return "stop"
        except BaseException as e:
            self.last_traceback = sys.exc_info()
            _display_runtime_error(e)
        return "continue"

    def _process_directives(self, command: str):
        if command.strip() == "quit!":
            print("Bye for now.")
            return "stop"
        elif command.strip() == "traceback?":
            self._print_last_traceback()
            return "continue"
        else:
            return None

    def _print_last_traceback(self):
        if self.last_traceback is None:
            print("No traceback :-)")
        else:
            traceback.print_exception(*last_traceback)  # type: ignore


def repl():
    Repl().run()
