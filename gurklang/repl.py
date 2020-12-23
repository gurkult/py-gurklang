"""
Read Eval Print Loop

The essential interactive programming tool!
"""
import sys
import traceback
from typing import Any

from colorama import init, Fore, Back
Fore: Any
Back: Any
init()

from .types import Code, CodeFlags
from .vm import run, call, make_scope
from .parser import parse, ParseError



def _get_input():
    try:
        return input(Fore.CYAN + ">>> " + Fore.RESET)
    except BaseException:
        print()
        return "quit!"


def print_red(*xs: Any):
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


def code(source: str) -> Code:
    parsed = parse(source)
    # PARENT_SCOPE is needed because otherwise, all of our names
    # (including imports) will vanish, as the scope will be popped
    return Code(parsed, name="<input>", closure=None, flags=CodeFlags.PARENT_SCOPE)


def repl():
    last_traceback = None

    stack, scope = run([])
    scope = make_scope(scope)  # we need to make our own scope not to change builtins
    stack, scope = call(stack, scope, code(":repl-utils :all import"))
    while True:
        command = _get_input()

        if command.strip() == "quit!":
            print("Bye for now.")
            break
        elif command.strip() == "traceback?":
            if last_traceback is not None:
                traceback.print_exception(*last_traceback)  # type: ignore
            continue

        try:
            stack, scope = call(stack, scope, code(command))
        except ParseError as e:
            _display_parse_error(e)
        except KeyboardInterrupt as e:
            print(Fore.RED + "CTRL + C" + Fore.RESET)
            break
        except BaseException as e:
            last_traceback = sys.exc_info()
            print(Fore.RED + type(e).__name__ + ": " + " ".join(e.args) + Fore.RESET)
            print(Fore.YELLOW + "Type traceback? for complete Python traceback" + Fore.RESET)
