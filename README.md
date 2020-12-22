# Gurklang

For details about the language, see `specification.md`.

# Project structure

---

## Tests

Tests are located in `tests/`. Just in case you're confused :)

---

## Implementation

Here I'll briefly descibe all modules.


### parser_utils.py

Parsing utilities used in `parser.py`. You probably don't need to read or
change this code.


### parser.py

Implementation of parsing. Exports a single `parse` function -- it accepts
Gurklang source code and returns a list of instructions.


### types.py

Definitions of types used across the project.

`Scope` represents a local scope. It's also used for implementing
module scopes and the global scope, since they obey the same rules.

The purpose of each instruction ("opcode") are described in the code.
If you're confused about any of that, you can use `inspect.dis` to dump
instructions of a function:
```elixir
:inspect :prefix import
:math ( + - < * ) import

{
  dup 2 <
  { drop 1 } parent-scope
  { dup 1 - n! * } parent-scope
  if !
} parent-scope :n! jar

:n! inspect.dis
```

All values are defined here as well. They map precisely to Gurklang values.


### vm_utils.py

Utilities used by the implementation and the standard library modules.


### vm.py

This module implements the core logic behind the interpreter.


### builtin_utils.py

Utilities for implementing standard library modules. For an example, see
`prelude.py` or any module in `stdlib_modules/`


### prelude.py

Implementation of the prelude, i.e. the functions that are available without
importing anything.
