# Almost-formal specification

---

# Overview

Gurklang is a dynamically typed stack-based language, taking some ideas from
functional programming.


# Syntax

A valid Gurklang program is a sequence of words, separated by spaces where necessary.

A comment, like `# Increment i`, is considered whitespace.

Possible word types:

| Name          | Explanation   | Example |
| ------------- | ------------- | ------- |
| Integer | sequence of digits, optionally preceded by `+` or `-` | `42` |
| String | sequence of characters enclosed in `""` or `''`, following common escaping rules|`"hello\nworld"`|
| Name | any sequence of non-whitespace characters other than `"'(){}#` not beginning with `:` and not forming an _integer_  | `foo`, `два-ℕ` |
| Atom | One or more colons `:` succeeded by a _name_ without whitespace | `:foo`, `::ba:r`, `:два-ℕ` |
| Code value | A valid program enclosed in `{` and `}` | `{ :foo 5 build }` |
| Tuple | A sequence of (possibly mixed) names, atoms*, integers, strings, code values enclosed in `(` `)` | `(rectangle 3 5)` |

`*` Note that `::foo` is the atom with the name `":foo"`, and `(foo :bar)` is a tuple containing atoms `:foo` and `::bar`.

Example of a valid program:
```elixir
{ :x def { x + } } :make_adder jar
5 make_adder :add5 jar

"Meaning of life, the universe and everything: " print
37 add5 println
```


# Semantics

## Overview

The progam is a sequence of instruction modifying two values:

* The stack
* The scope tree

All words besides names, like `+` or `add` are called **_literal words_**. All
they do is put a single literal value on top of the stack.

For example, the program `1 2 3` puts the integers `1`, `2`, and `3` on the stack.
It means that `3` will be the top element, `2` is the beneath `3`, and `1` is
beneath `2`.

A name word represents a function call. A _function_ can be thought of as an action
which is given a name, and a _function call_ is the act of executing that action.

* A function usually only changes the stack. For example, The `+` function grabs
the top two elements of the stack and, assuming they're integers, puts their
sum on the stack.

* Some functions can create local variables. For example, The `def` function creates
a local variable given an atom and a value. This program puts `6` on the stack:
```elixir
1 :x def
2 :y def

x y  + y *
```
What `def` actually does is: it captures the top value of the stack and creates
a function, named the same as the atom, that puts that value onto the stack.

* "Variables" aren't reassignable. You can only assign a value to a name once
in a scope. For example, this will fail at runtime:
```elixir
1 :x def
2 :x def
```

* Some functions produce _side effects_: print something to the screen, send a
request to a web service, or launch nuclear missiles. And example would be the
`print` function:
```elixir
"Hello, world!" print
```

## Values explaned

### Integer values

An integer value is an arbitrarily large whole number.

### String values

A string value is a sequence of Unicode codepoints

### Atom values

An atom value is a unique identifier that can be stored and compared efficiently

### Native function values

A native function is a function implemented in the host language, not in terms
of Gurklang itself.

### Code values

A code value is a user-defined function, combining a sequence of instrunctions
and a closure. They're explained in more detail later.

### Tuple values

A tuple is an ordered collection of values.

### Box values

A "box" is a mutable variable.


## Code values

A syntactically valid program enclosed in `{` `}` is a _code value_ word. It's a literal
word, so all it does is put a code value onto the stack. A code value represents
a user-defined function and consists of a sequence of words.

To run a code value, you can use the built-in `!` function. For example, these programs do the same:
```elixir
2 3 +

{ 2 3 + } !

2 { 3 + } !

{ { 2 } ! { 3 + } ! }  !
```

You can store a code value by a name using the `jar` function, which acts
similarly to `def`:
```elixir
{ 3 + } :add3 jar

10 add3 print  # output: 13
```
The difference between `def` and `jar` is that `def` create a function that
puts a given value on the stack. So
```elixir
{...} :x jar
# ...
x
```
 is the same as
```elixir
{...} :x def
# ...
x !
```


## Local scopes

When a code value is ran, it is allocated its own local scope,
so calling `def` or `jar` inside of it will not alter the global scope, but
only create local variables. Example:

```elixir
5 :x def

{ :x def x x + } :double def

10 double print  # output: 20
x print          # output: 5
```


## Parent-scoped functions
A function can be made "parent-scoped" with `parent-scope`. It means that the
function will not reserve a local scope when called.

```elixir
{ 6 :x def } parent-scope !
x println  # 6
```


## Closures

A code value creates inside another code value can capture a part of its local scope
to persist after the outer function is exited. For example, this is how you can
create a function `f` that puts `5` three times on the stack:

```elixir
{ :x def { x x x } } :make-putter jar

5 make-putter :f jar

f + * print  # output: 50
```
Here, `make-putter` creates a code value that has access to the local variable `x`
of the outer scope. When `make-putter` is done running, the code value that escapes
it has access to the `x` variable.
