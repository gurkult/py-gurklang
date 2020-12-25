"""
Read Eval Print Loop

The essential interactive programming tool!
"""
from gurklang.vm_utils import render_value_as_source
import sys
import traceback
from typing import Any, Callable, Optional, TextIO, Tuple

from colorama import init, Fore, Style
Fore: Any
Style: Any
init()

from .types import Code, CodeFlags, Instruction, Scope, Stack, State, Value
from .vm import call_with_middleware, run, call, make_scope
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


class StdoutSniper:
    """
    Wait for something to start writing to stdout and do something before doing so
    """
    def __init__(
        self,
        real_stdout: TextIO,
        on_start: Callable[[TextIO], None],
        on_end: Callable[[TextIO], None],
    ):
        self.real_stdout = real_stdout
        self.on_start = on_start
        self.on_end = on_end
        self._watching = False
        self._was_triggered = False

    def watch(self):
        self._watching = True
        self._was_triggered = False

    def unwatch(self):
        self._watching = False
        if self._was_triggered:
            self.on_end(self.real_stdout)
            self._was_triggered = False

    def write(self, s: str):
        if self._watching:
            self._was_triggered = True
            self.on_start(self.real_stdout)
            self._watching = False
        self.real_stdout.write(s)
        self.real_stdout.flush()

    def flush(self):
        pass


DEFAULT_PRELUDE = R"""
:repl-utils :all                               import
:inspect    :prefix                            import
:coro       :prefix                            import
:math       ( < + - * / % %make %+ %- %* %/ )  import


{
  ">>> " :repl[prompt]        var
  ""     :repl[before-output] var
  ""     :repl[after-output]  var
  "<-- " :repl[before-stack]  var
}
parent-scope :repl[style:default] jar


{
  "│ "                     :repl[prompt]        var
  "└───────────────────\n" :repl[before-output] var
  ""                       :repl[after-output]  var
  "├─"                     :repl[before-stack]  var
}
parent-scope :repl[style:box] jar


{
  "│\n│ "                     :repl[prompt]        var
  "└───────────────────\n" :repl[before-output] var
  "\n"                       :repl[after-output]  var
  "│\n╞═"                     :repl[before-stack]  var
}
parent-scope :repl[style:box-wide] jar


{
  "In:\n" :repl[prompt]        var
  "Out:\n" :repl[before-output] var
  "\n"      :repl[after-output]  var
  "Stack:\n" :repl[before-stack]  var
}
parent-scope :repl[style:in-out] jar


{ :true :repl[display-stack] var }
parent-scope :show-stack jar


{ :false :repl[display-stack] var }
parent-scope :hide-stack jar


repl[style:default]
hide-stack


"Gurklang v0.0.1" println
"---------------" println
"""


class ExitDebug(BaseException):
    pass


class Repl:
    stack: Stack
    scope: Scope
    last_traceback: Optional[Tuple[Any, Any, Any]]

    def __init__(self, prelude: str = DEFAULT_PRELUDE):
        state = run([])
        local_scope = make_scope(state.scope)
        state = state.with_scope(local_scope)
        state = call(state, code(prelude))
        self.state = state
        self.last_traceback = None
        self.sniper = StdoutSniper(
            sys.stdout,
            self._before_printing_occurs,
            self._after_printing_occurs,
        )
        sys.stdout = self.sniper

    # Command processing:

    def run(self):
        action = "continue"
        while action != "stop":
            command = self._get_input()
            action = self._process_command(command)

    def _get_input(self):
        try:
            return input(Fore.CYAN + self._prompt + Fore.RESET)
        except (EOFError, KeyboardInterrupt):
            print()
            return "quit!"

    def _process_command(self, command: str):
        return (
            self._process_directives(command)
            or self._run_with_error_handling(command, lambda: call(self.state, code(command)))
        )

    def _run_with_error_handling(self, source_code: str, run: Callable[[], State]):
        self.sniper.watch()
        try:
            self.state = run()
        except ParseError as e:
            _display_parse_error(e)
        except KeyboardInterrupt as e:
            print_red("CTRL + C")
            return "stop"
        except BaseException as e:
            self.last_traceback = sys.exc_info()
            _display_runtime_error(e)
        finally:
            self.sniper.unwatch()
            self._display_stack_if_on()
        return "continue"

    def _debug(self, source_code: str):
        def on_next_step(i: Instruction, old_stack: Stack, new_stack: Stack):
            self._display_stack(self.state.with_stack(new_stack))
            cmd = input("'next' or 'exit' (next): ")
            if cmd == "exit":
                raise ExitDebug

        def run():
            try:
                resulting_state = call_with_middleware(self.state, code(source_code), middleware=on_next_step)
                self._display_stack(resulting_state)
                if input("accept the resulting state? y/n (n): ") in ("y", "yes", "1"):
                    return resulting_state
            except ExitDebug:
                print_red("debug mode exited")
            return self.state

        self._run_with_error_handling(source_code, run)

    def _process_directives(self, command: str):
        command = command.strip()
        if command == "quit!":
            print("Bye for now.")
            return "stop"
        elif command == "traceback?":
            self._print_last_traceback()
            return "continue"
        elif command.startswith("debug!"):
            source_code = command[len("debug!"):]
            self._debug(source_code)
            return "continue"
        else:
            return None

    def _print_last_traceback(self):
        if self.last_traceback is None:
            print("No traceback :-)")
        else:
            traceback.print_exception(*self.last_traceback)  # type: ignore

    # StdoutSniper integration:

    def __del__(self):
        sys.stdout = self.sniper.real_stdout

    def _before_printing_occurs(self, writer: TextIO):
        s = self._string_before_output
        if s != "":
            writer.write(Fore.CYAN + s + Fore.RESET)

    def _after_printing_occurs(self, writer: TextIO):
        s = self._string_after_output
        if s != "":
            writer.write(Fore.CYAN + s + Fore.RESET)

    def _display_stack_if_on(self):
        if self._is_stack_display_on:
            self._display_stack(self.state)

    def _display_stack(self, state: State):
        print(Fore.CYAN + self._string_before_stack + Fore.YELLOW + Style.BRIGHT, end="")
        call(state, code("12 stack-repr print"))
        print(Fore.RESET + Style.RESET_ALL)

    # Interacting with configuration:

    def _run_code_for_side_effect(self, source_code: str):
        call(self.state, code(source_code))

    def _run_code_for_single_value(self, source_code: str) -> Value:
        state = call(self.state, code(source_code))
        if state.stack is None:
            raise RuntimeError(f"Stack is unexpectedly empty at code: {code}")
        (head, _rest) = state.stack
        return head

    def _get_str_config_value(self, label: str) -> str:
        str_ = self._run_code_for_single_value(f"repl[{label}]")
        if str_.tag != "str":
            raise RuntimeError(f"Expected string for `repl[{label}]`, got {str_}")
        return str_.value

    def _get_bool_config_value(self, label: str) -> bool:
        atom = self._run_code_for_single_value(f"repl[{label}]")
        if atom.tag != "atom":
            raise RuntimeError(f"Expected atom for `repl[{label}]`, got {atom}")
        if atom.value not in ["true", "false"]:
            raise RuntimeError(f"Expected :true or :False for `repl[{label}]`, got {atom}")
        return atom.value == "true"

    @property
    def _string_before_stack(self) -> str:
        return self._get_str_config_value("before-stack")

    @property
    def _string_before_output(self) -> str:
        return self._get_str_config_value("before-output")

    @property
    def _string_after_output(self) -> str:
        return self._get_str_config_value("after-output")

    @property
    def _prompt(self) -> str:
        return self._get_str_config_value("prompt")

    @property
    def _is_stack_display_on(self) -> bool:
        return self._get_bool_config_value("display-stack")


def repl():
    Repl().run()
