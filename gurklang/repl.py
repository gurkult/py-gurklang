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


def repl():
    last_traceback = None

    stack, scope = run([])
    scope = make_scope(scope)  # we need to make our own scope not to change builtins
    stack, scope = call(stack, scope, Code(parse(r":repl-utils :all import"), closure=None, flags=CodeFlags.PARENT_SCOPE))
    while True:
        try:
            command = input(Fore.CYAN + ">>> " + Fore.RESET)
        except BaseException:
            command = "quit!"
            print()

        if command.strip() == "quit!":
            print("Bye for now.")
            break
        elif command.strip() == "traceback?":
            if last_traceback is None:
                print("No traceback :-)")
            else:
                traceback.print_exception(*last_traceback)  # type: ignore
            continue

        try:
            parsed = parse(command)
        except ParseError as e:
            if e.is_eof:
                print(Fore.RED + f"Unexpected EOF while parsing {e.while_parsing_what}" + Fore.RESET)
            else:
                t = e.token
                print(
                    Fore.RED
                    + f"Syntax error at {t.position} in token '{t.value}' ({t.name})"
                    + f" while parsing {e.while_parsing_what}"
                    + Fore.RESET
                )
            continue

        try:
            stack, scope = call(stack, scope, Code(parsed, None, name="<input>", source_code=command, flags=CodeFlags.PARENT_SCOPE))
        except KeyboardInterrupt as e:
            print(Fore.RED + "CTRL + C" + Fore.RESET)
            break
        except BaseException as e:
            last_traceback = sys.exc_info()
            print(Fore.RED + type(e).__name__ + ": " + " ".join(e.args) + Fore.RESET)
            print(Fore.YELLOW + "Type traceback? for complete Python traceback" + Fore.RESET)
