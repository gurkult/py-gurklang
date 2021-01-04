"""
Read Eval Print Loop

The essential interactive programming tool!
"""
from __future__ import annotations
from .vm_utils import render_value_as_source, stringify_stack
from . import vm
from .repl_constants import DEFAULT_PRELUDE, BACKSLASH_MAPPING
import sys
import traceback
from typing import Any, Callable, Iterable, Iterator, Optional, TextIO, Tuple

import click

from colorama import init, Fore, Style
Fore: Any
Style: Any
init()

from .types import Code, CodeFlags, Instruction, Stack, State, Value
from .vm import call_with_middleware, run, call, make_scope
from .parser import parse, lex, ParseError



ENTER = chr(13)
BACKSPACE = (chr(127), chr(0x08))

is_backspace = BACKSPACE.__contains__


def backspace(size: int = 1):
    click.echo("\b" * size, nl=False)
    click.echo(" " * size, nl=False)
    click.echo("\b" * size, nl=False)


def inline_error_message(message: str):
    click.secho(message, color=True, fg="white", bg="red", nl=False)
    click.getchar(echo=False)
    backspace(len(message))


def suggest_inline_variants(variants: Iterable[Any], fg: str = "white", bg: str = "blue"):
    message = " ".join(variants)
    click.secho(message, color=True, fg=fg, bg=bg, dim=True, nl=False)
    click.getchar(echo=False)
    backspace(len(message))


def print_red(*xs):
    print(Fore.RED, end="")
    print(*xs, end="")
    print(Fore.RESET)


def _display_parse_error(e: ParseError):
    if e.is_eof():
        print_red("Unexpected EOF while parsing", e.while_parsing_what, repr(e.token))
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


class SyntaxHighlighter:
    def __init__(self, repl: Repl):
        self.repl = repl

    def _colorize_line(self, source_line: str) -> Iterator[str]:
        last_end_pos = -1
        for token in lex(source_line):
            if token.position > last_end_pos + 1:  # we've got whitespace
                ws = source_line[last_end_pos + 1 : token.position]
                yield Fore.LIGHTGREEN_EX + Style.DIM + ws + Style.RESET_ALL + Fore.RESET

            if token.name == "STRING":
                yield Fore.GREEN + token.value + Fore.RESET

            elif token.name == "INT":
                yield Fore.CYAN + token.value + Fore.RESET

            elif token.name == "ATOM":
                yield Fore.RED + token.value + Fore.RESET

            elif token.name == "NAME":
                yield Style.BRIGHT + Fore.YELLOW + token.value + Fore.RESET + Style.RESET_ALL

            else:
                yield token.value

            last_end_pos = token.position + len(token.value) - 1

        if last_end_pos != len(source_line):  # some whitespace is left
            yield Fore.WHITE + Style.DIM + source_line[last_end_pos + 1:] + Style.RESET_ALL + Fore.RESET


    def colorize_source_line(self, source_line: str):
        return "".join(self._colorize_line(source_line))


class InputMethod:
    def __init__(self, repl: Repl):
        self.repl = repl
        self.highlighter = SyntaxHighlighter(repl)

    def get_multiline_input(self, on_parse_error: Callable[[ParseError], None]) -> str:
        # TODO: refactor this method
        lines = []

        indentation = ""
        while True:
            prompt = self.repl.config.prompt if lines == [] else self.repl.config.multiline_prompt
            print(Fore.CYAN + Style.DIM + prompt + Style.RESET_ALL + Fore.RESET, end="")
            line = indentation
            print(line, end="")
            try:
                done = False
                while not done:
                    done, line = self. _process_next_character(line)
                lines.append(line)
            except (EOFError, KeyboardInterrupt):
                print()
                if lines == []:
                    return "quit!"
                else:
                    return ""

            try:
                parse("\n".join(lines))
                break
            except ParseError as e:
                if not e.is_eof():
                    on_parse_error(e)
                    return ""

            last_indent_size = len(lines[-1]) - len(lines[-1].lstrip())
            indentation = " " * last_indent_size
        return "\n".join(lines)

    def _process_next_character(self, old_line: str):
        """
        Get the next character and decide what the new line state should be.

        Returns:
            0. Is it the end of the line?
            1. The new line state
        """
        char = click.getchar(echo=False)

        if char == "\\":
            new_line = old_line + self._process_backslash_escape()
        elif len(char) == 1 and char.isprintable():
            new_line = old_line + char
        elif char == "\t":
            new_line = old_line + "  "
        elif is_backspace(char):
            new_line = old_line[:-1]
        else:
            new_line = old_line

        backspace(len(old_line))
        print(self.highlighter.colorize_source_line(new_line), end="")

        if char == ENTER:
            print()
            return True, new_line
        else:
            return False, new_line

    def _process_backslash_escape(self) -> str:
        accumulated = ""

        click.secho("\\", color=True, fg="white", bg="blue", nl=False)

        while True:
            done, new_acc = self._next_backslash_step(accumulated)
            if done:
                return new_acc

            backspace(len(accumulated) + 1)
            bg, bold = ("green", True) if new_acc in BACKSLASH_MAPPING else ("blue", False)
            click.secho("\\" + new_acc, color=True, bg=bg, bold=bold, nl=False)

            accumulated = new_acc

    def _next_backslash_step(self, accumulated: str):
        char = click.getchar(echo=False)
        if char == "\\":
            if accumulated == "":
                backspace()
                return True, "\\"
        elif char in (" ", ENTER, "\t") and accumulated != "":
            # lam -> [("bda", "λ")]
            completions = [(k[len(accumulated):], v) for k, v in BACKSLASH_MAPPING.prefix_search(accumulated)]

            if accumulated in BACKSLASH_MAPPING:
                backspace(len(accumulated) + 1)
                return True, BACKSLASH_MAPPING[accumulated]
            elif len(completions) == 1:
                backspace(len(accumulated) + 1)
                return True, BACKSLASH_MAPPING[accumulated + completions[0][0]]
            elif completions == []:
                inline_error_message("not found")
            else:
                suggest_inline_variants(
                    f"{completion}({result})" for completion, result in completions
                )
        elif is_backspace(char):
            if accumulated == "":
                backspace()
                return True, ""
            else:
                return False, accumulated[:-1]
        elif len(char) == 1 and char.isprintable():
            return False, accumulated + char
        return False, accumulated


class ReplConfig:
    def __init__(self, repl: Repl):
        self.repl = repl

    @property
    def string_before_stack(self) -> str:
        return self._get_str_config_value("before-stack")

    @property
    def string_before_output(self) -> str:
        return self._get_str_config_value("before-output")

    @property
    def string_after_output(self) -> str:
        return self._get_str_config_value("after-output")

    @property
    def prompt(self) -> str:
        return self._get_str_config_value("prompt")

    @property
    def multiline_prompt(self) -> str:
        return self._get_str_config_value("ml-prompt")

    @property
    def is_stack_display_on(self) -> bool:
        return self._get_bool_config_value("display-stack")

    def _run_code_for_single_value(self, source_code: str) -> Value:
        state = call(self.repl.state, code(source_code))
        if state.stack is None:
            raise RuntimeError(f"Stack is unexpectedly empty at code: {code}")
        (head, _rest) = state.stack
        return head

    def _get_str_config_value(self, label: str) -> str:
        str_ = self._run_code_for_single_value(f"repl[{label}] ->")
        if str_.tag != "str":
            raise RuntimeError(f"Expected string for `repl[{label}]`, got {str_}")
        return str_.value

    def _get_bool_config_value(self, label: str) -> bool:
        atom = self._run_code_for_single_value(f"repl[{label}] ->")
        if atom.tag != "atom":
            raise RuntimeError(f"Expected atom for `repl[{label}]`, got {atom}")
        if atom.value not in ["true", "false"]:
            raise RuntimeError(f"Expected :true or :False for `repl[{label}]`, got {atom}")
        return atom.value == "true"


class Repl:
    last_traceback: Optional[Tuple[Any, Any, Any]]

    class ExitDebug(BaseException):
        pass

    def __init__(self, prelude: str = DEFAULT_PRELUDE, program: str = ""):
        state = run([])
        state = call(state, code(program))
        self.state = call(state, code(prelude))
        self.last_traceback = None

        self.sniper = StdoutSniper(
            sys.stdout,
            self._before_printing_occurs,
            self._after_printing_occurs,
        )
        sys.stdout = self.sniper

        self.config = ReplConfig(self)
        self.input_method = InputMethod(self)

    # Entry point:

    def run(self):
        action = "continue"
        while action != "stop":
            command = self.input_method.get_multiline_input(_display_parse_error)
            action = self._process_command(command)

    # Command processing:

    def _process_command(self, command: str):
        return (
            self._process_directives(command)
            or self._run_with_error_handling(lambda: call(self.state, code(command)))
        )

    def _run_with_error_handling(self, run: Callable[[], State]):
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
            self._display_stack_with_instruction(new_stack, i)
            cmd = input("'next' or 'exit' (next): ")
            if cmd == "exit":
                raise Repl.ExitDebug

        def run():
            self._display_stack(self.state.stack)
            try:
                resulting_state = call_with_middleware(self.state, code(source_code), middleware=on_next_step)
                self._display_stack(resulting_state.stack, color=Fore.GREEN)
                if input("accept the resulting state? y/n (n): ") in ("y", "yes", "1"):
                    return resulting_state
            except Repl.ExitDebug:
                print_red("debug mode exited")
            return self.state

        self._run_with_error_handling(run)

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
        if hasattr(self, "sniper"):
            sys.stdout = self.sniper.real_stdout

    def _before_printing_occurs(self, writer: TextIO):
        s = self.config.string_before_output
        if s != "":
            writer.write(Fore.CYAN + s + Fore.RESET)

    def _after_printing_occurs(self, writer: TextIO):
        s = self.config.string_after_output
        if s != "":
            writer.write(Fore.CYAN + s + Fore.RESET)

    # Displaying the stack:

    def _display_stack_if_on(self):
        if self.config.is_stack_display_on:
            self._display_stack(self.state.stack)

    def _display_stack(self, stack: Stack, color=Fore.YELLOW):
        print(Fore.CYAN + self.config.string_before_stack + color + Style.BRIGHT, end="")
        print(stringify_stack(stack, max_depth=12) + Fore.RESET + Style.RESET_ALL)

    def _display_stack_with_instruction(self, stack: Stack, instruction: Instruction):
        stack_repr = stringify_stack(stack, max_depth=10)
        padded_stack_repr = stack_repr.ljust(50)
        instruction_repr = render_value_as_source(instruction.as_vec())
        print(
            Fore.CYAN
            + self.config.string_before_stack
            + Fore.YELLOW
            + Style.BRIGHT
            + padded_stack_repr
            + Fore.GREEN
            + instruction_repr
            + Fore.RESET
            + Style.RESET_ALL
        )


def repl():
    Repl().run()


def run_and_open_repl(source: str):
    Repl(program=source).run()
