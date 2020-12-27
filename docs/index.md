# Welcome to the Gurklang documenation!

Gurklang is a

- stack-based
- dynamically typed
- functional

programming language.

## What is...

### ..."stack-based"?

In Gurklang, all operations manipulate a _stack_ in some way:

```gurk
>>>
>>> peek
()
>>> 1
>>> peek
(1 ())
>>> 2
>>> peek
(2 (1 ()))
>>> 3 4
>>> peek
(4 (3 (2 (1 ()))))
>>>
```

- You start with a clean slate &mdash; an empty stack, denoted as `()`.
- When you run the command `1`, you push the number `1` on top of the stack,
and you end up with `(1 ())`, which means: `1`, then the empty stack.
- When you run the command `2`, you push the number `2` on top of the stack,
and you end up with `(2 (1 ()))`, which means: `2`, then `1`, then the empty stack.
- Running `peek` simply prints the value of the stack

Creating numbers isn't very exciting. Let's destroy them!
```gurk
>>> peek
(4 (3 (2 (1 ()))))
>>> drop
>>> peek
(3 (2 (1 ())))
>>> drop drop
>>> peek
(1 ())
```
As you can see, `drop` simply discards the top value on the stack.


`dup`, on the other hand, duplicates the top value on the stack:
```gurk
>>> peek
(1 ())
>>> dup peek
(1 (1 ()))
>>> dup peek
(1 (1 (1 ())))
```

You can also do maths!
```gurk
>>> peek
(1 (1 (1 ())))
>>> + peek
(2 (1 ()))
>>> + peek
(3 ())
>>> 14 peek
(14 (3 ()))
>>> * peek
(42 ())
```
`+`, `*`, `-` pick the top two elements on the stack, do the respective
operation on them, and put the result back on the stack.

Like in most programming languages, there are strings:
```gurk
>>> 'Hello, world!'
>>> peek
('Hello, world' ())
>>> println
Hello, world!
>>> "Hello, world!" println
Hello, world!
```
As you can see, both double and single quotes work.

If you're just tired of spelling out some value every time, you can define a
name!
```gurk
>>> 42 :answer var
>>> "Hello, world!" :greeting var
>>> answer peek
(42 ())
>>> greeting peek
('Hello, world' (42 ()))
>>> drop drop
```

You can also define your own functions, which is the most important aspect of
the language, but more on that later:
```gurk
>>> { dup dup println println println } :3print jar
>>>
>>> "Hello," 3print "How low" println
Hello,
Hello,
Hello,
How low
>>>
```

### ..."dynamically typed"?

While each value has a fixed type (e.g. an integer, a string, a function),
type soundness is not statically determined.

On one hand, dynamic typing delays type errors until runtime:
```gurk
>>> { dup + } :double jar
>>> 5 double println
10
>>> "a" double println
```
```plaintext
Failure in function +
Reason: Str(value='a') cannot be added with Str(value='a')
> Stack:  [1 2 3 4 a a]
Failure in function +
Reason: uncaught exception RuntimeError: + Str(value='a') cannot be added with Str(value='a')
> Stack:  [1 2 3 4 a a]
RuntimeError: + uncaught exception RuntimeError: + Str(value='a') cannot be added with Str(value='a')
Type traceback? for complete Python traceback
```

On the other hand, you get more flexibility. You can easily define a function
that works on one type, two types, all types, or can even take a variable
number of arguments from the stack.

Fun fact: a dynamically typed language will never reject a valid program!


### "...functional"?

Gurklang is influenced by functional programming languages, like Clojure and Haskell.
Functional programming emphasizes:

- Higher-order functions &mdash; functions that operate on functions
    ```gurk
    >>> 5 peek
    (5 ())
    >>> { 2 + }
    ({2 +} (5 ()))
    >>> !
    >>> peek
    (7 ())
    ```
    ```gurk
    >>> { :f var  f ! f ! } :do-twice jar
    >>> 5
    >>> peek
    (5 ())
    >>> { 2 + } do-twice
    >>> peek
    (9 ())
    ```

- Immutability: a definition is not a _variable_ &mdash; you can't reassign it.
    ```gurk
    >>> 3 :pi var
    >>> 3 :e  var
    >>> 2 :e  var
    ```
    ```plaintext
    Failure in function var
    Reason: uncaught exception RuntimeError: Trying to reassign e
    > Stack:  [9 2 :e]
    RuntimeError: var uncaught exception RuntimeError: Trying to reassign e
    Type traceback? for complete Python traceback
    ```
    There is a mechanism for managing mutable variables, but you'll rarely need it.

- Expressive language and rich standard library
    ```gurk
    >>> :coro :all import
    >>> {
    ...   swap dup
    ...   println
    ...   (1 10) sleep
    ...   swap dup rot +
    ... }
    ... parent-scope
    ... (1 (1 ()))
    ... :fib generator
    ...
    >>> fib forever
    1
    1
    2
    3
    5
    8
    ...
    ```

- Strong typing: don't hide errors, bring them out!
    ```gurk
    >>> 1 2 =
    >>> println
    :false
    >>> 1 1 =
    >>> println
    :true
    >>> 1 "foo" =
    ```
    ```plaintext
    Failure in function =
    Reason: cannot compare type int with type str
    > Stack:  [9 1 foo]
    Failure in function =
    Reason: uncaught exception RuntimeError: = cannot compare type int with type str
    > Stack:  [9 1 foo]
    RuntimeError: = uncaught exception RuntimeError: = cannot compare type int with type str
    Type traceback? for complete Python traceback
    ```

- Great recursion support
    ```gurk
    >>> { dup 2 <
    ...   { drop 1 }
    ...   { dup 1 - n! * } parent-scope
    ...   if !
    ... } parent-scope :n! jar
    ...
    >>> 2000 n! println
    33162750924506332411753933805763240...
    >>>
    ```
