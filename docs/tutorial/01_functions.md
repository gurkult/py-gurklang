# Creating your own functions

A function is a way of establishing a simpler, smaller program inside of a bigger one.

Suppose that you need to write a function that finds $2^5$. It's not very hard:

%%%gurkrepl
>>> 2 2 2 2 2
>>> * * * *
>>> println
32
>>>
%%%

But then you might want to find $3^5$, and $6^5$, and even $8^{13}$. Instead
of typing out essentially the same code again and again, you can create a
function:
%%%gurkrepl
>>> { dup dup dup dup * * * * } :^5 jar
>>> 2 ^5
>>> peek
(32 ())
>>>
%%%

`jar` stores a sequence of commands. When you call `^5`, it executes them,
as if you wrote the same sequence of instructions manually:
%%%gurkrepl
>>> 2 dup dup dup dup * * * *
>>> println
32
>>>
%%%

Functions are useful because they allow you to name a certain action and
refer to it many times, in different contexts.
%%%gurkrepl
>>> 3 ^5 println
243
>>> 4 ^5 println
1024
>>>
%%%

Let's look at a function definition in parts. First, you need to write a
_code literal_. It's a Gurklang program, written between `{` and `}`.
%%%gurk
#((
{ dup dup dup dup * * * * }
#))
:^5
jar
%%%

Then, we need to give our function a name. It must be an atom, like with `def`.
%%%gurk
{ dup dup dup dup * * * * }
#((
:^5
#))
jar
%%%

Finally, we call the built-in `jar` function to store a function under a name.
%%%gurk
{ dup dup dup dup * * * * }
:^5
#((
jar
#))
%%%

Why can't use use `def` to define functions? Well, let's try.
%%%gurkrepl
>>> :^5 forget
Sending ^5 to the shredder... done.
>>> { dup dup dup dup * * * * } :^5 def
>>> 2 ^5
>>> println
{ dup dup dup dup * * * * }
>>> peek
(2 ())
%%%
`def`ining a function like this just stores the code, so when you invoke `^5`,
you put the function on top of the stack. You can call the built-in
`!` function to call a function which is on top of the stack:
%%%gurkrepl
>>> 2 ^5 ! println
32
>>>
%%%

In fact, you can call a function without giving it a name:
%%%gurkrepl
>>> 2 { 3 + } ! println
5
>>> 2 { dup dup dup dup * * * * } ! println
32
>>>
%%%

!!! info
    A function name can be anything you like, except:

    - it can't contain `{}()'"`

    - it can't be a number, like `23`, `-4`, or `+128`

    You can give functions crazy names, like: `≤`, `empty?`, `∀x∈ℕ`, `[🐝ПЧЕЛА🐝]`.

    This is a powerful and dangerous ability. Try to stick to English words,
    except for common mathematical operators.

# Combining functions

You can use functions to define other functions. For example:
%%%gurkrepl
>>> { "*" print } :star jar
>>> { "*" println } :star-nl jar
>>>
>>> { star star star star-nl } :star-row jar
>>>
>>> { star-row star-nl star-row star-nl star-nl } :F jar
>>>
>>> F
****
*
****
*
*
>>> { (1 2) sleep F Fs } :Fs jar
>>> Fs
****
*
****
*
*
****
*
****
*
*
...
%%%

# Functions are values

Remember how `!` calls a function that's on top of the stack? That's an example
of how you can use functions as _values_: functions are ordinary "things" like
numbers and strings, not just collections of instructions.

This is how you can create a function that, given a function, puts 5 on the stack
and executes the function:
%%%gurkrepl
>>> { 5 swap ! } :!5 jar
>>> { 37 + println } !5
42
>>>
%%%

!!! info
    Functions that work with other functions as values
    are called _higher-order functions_

Another useful built-in function is `close`. It consumes a function and a value,
and returns a new function which is like the old one, but puts the value on the
stack before running. Example:
%%%gurkrepl
>>> 1 { 2 } close :f jar
>>> f
>>> peek
(2 (1 ()))
%%%
Here `close` "adds" `1` to the start of `{ 2 }`, and a new function with the
body `{ 1 2 }` is created.

Another example:
%%%gurkrepl
>>> { {+} close } :make-adder jar
>>> 37 5 make-adder
>>> peek
({...} (37 ()))
>>> ! println
42
%%%
In the above snippet, `make-adder` is a function that accepts an integer and
gives back a function that adds this integer: `5 make-adder` is the same as `{5 +}`.
You can store this function as well:

%%%gurkrepl
>>> 5 make-adder :5+ jar
>>> 37 5+ println
42
%%%

# `def` inside functions

You can use `def` to define names inside a function. After the function has
stopped running, the name vanishes.

%%%gurkrepl
>>> { 5 :x def  x println  x println } :f jar
>>> f
5
5
>>> x
KeyError: x
Type traceback? for complete Python traceback
%%%

You can use `def` inside a function to store some value from the stack
and then refer to it:
%%%gurkrepl
>>> { :x def :y def
...   x x *
...   y y *
...   +
... } :sum-squares jar
>>> 3 4 sum-squares println
25
%%%
When you execute a function, it creates its own little bubble, called its
_local scope_. Inside that scope, you can define new names. They will disappear
when the function is done running.

# Beyond the basics

## Parent-scoped functions

You can mark a function as "parent-scoped" if it shouldn't create a local
scope, but instead should run in the scope of whoever executes it.

%%%gurkrepl
>>> { 1 :x def } parent-scope :f jar
>>> f
>>> x println
1
>>> f
>>> 2 :x def
Failure in function def
Reason: uncaught exception RuntimeError: Trying to reassign x
> Stack:  [2 :x]
RuntimeError: def uncaught exception RuntimeError: Trying to reassign x
Type traceback? for complete Python traceback
%%%

This is useful in two cases:

  * When you actually want to define a new name in the parent scope;

  * When you don't want to create a nested scope. This is crucial for so-called
  _tail call optimization_ in recursive functions. But more on that later.

## Defining `def`

Surprisingly or not, `def` creates a function as well. Here, `x` and `y` are
absolutely equivalent:

%%%gurk
6 :x def
{ 6 } :y jar
%%%

In fact, you can define `def` in terms of `jar`: `{ x } :name jar` is the same
as  `x :name var`. Try to define a `my-def` function that acts like `def`.


??? question "Answer"
    %%%gurk
    { swap {} close swap jar } parent-scope :my-def jar
    %%%

## Closures

Remind yourself of this example:
%%%gurkrepl
>>> { {+} close } :make-adder jar
>>> 37 5 make-adder
>>> peek
({...} (37 ()))
>>> ! println
42
%%%

You can do the same with names, without using `close`:
%%%gurkrepl
>>> { :x def {x +} } :make-adder jar
>>> 37 5 make-adder
>>> peek
({x +} (37 ()))
>>> ! println
42
%%%

When a function gives back another function, the old function's local scope
doesn't actually die &mdash; it's stored in the returned function so that
it can access the saved names.


## Exercises

### 1. `!!`

Write and test a function `!!` that accepts a function `(n -- n)` and an integer,
and first runs this function on the given integer, and then runs it again on the result.
%%%gurkrepl
>>> 5 {1 +} !! println
7
>>> 2 {dup * 1 +} !! println
26
>>> # 2 2 * 1 +  --  5
>>> # 5 5 * 1 +  --  26
%%%
Implement this function in two ways: using a closure and using only stack manipulations.

??? question "Answer"
    Using a closure:
    %%%gurk
    { :f def f ! f ! } :!! jar

    # bonus points if you came up with this:
    { :f jar f f } :!! jar
    # :-)
    %%%
    Using stack manipulations (one way, there are many):
    %%%gurk
    { swap over ! swap ! } :!! jar
    %%%

### 2. `forever`

Can you rewrite this function without using closures, so that it can be made
parent-scoped?

%%%gurkrepl
>>> { :f def f ! f forever } :forever jar
>>> { (1 5) sleep "Hello!" println } forever
Hello!
Hello!
Hello!
Hello!
...
%%%

??? question "Answer"
    %%%gurk
    { dup ! forever } parent-scope :forever jar
    %%%

Can you tell what will happen when you run this code?
%%%gurk
{ forever } forever
%%%

To test your prediction, use the debugger:
%%%gurkrepl
>>> debug! { forever } forever
%%%

### 3. `?`

Create two functions, `true : (f g -- g!)` and `false : (f g -- f!)`:
%%%gurkrepl
>>> {1} {2} true ! println
2
>>> {1} {2} false ! println
1
%%%
Implement both the closure version and the stack manipulation version.

??? question "Answer"
    Closure:
    %%%gurk
    # (f g -- g!)
    { :g jar :f jar g } :true var
    { :g def :f def g ! } :true var

    # (f g -- f!)
    { :g jar :f jar f } :false var
    { :g def :f def f ! } :false var
    %%%
    Stack juggling:
    %%%gurk
    # (f g -- g!)
    { swap drop ! } :true var

    # (f g -- f!)
    { drop ! } :false var
    %%%

Then write a function `?` that accepts a function and either `true` of `false`. If the
second value is `true`, it runs the function. Otherwise, it discards it.

%%%gurkrepl
>>> { "Hi!" println! } true ?
Hi
>>> { "Hi!" println! } false ?
>>>
%%%

??? question "Answer"
    %%%gurk
    { {} unrot ! } :? jar
    %%%
