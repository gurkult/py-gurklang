# Snippets

Useful fragments of documentation I'm not sure where to put

## Debugging

!!! note Debugging
If you're not sure how a program works, you can step through with a _debugger_.
A debugger is a tool that allows you to step through a program step by step
and see what it does.

To step through a command, type in `debug! <your command>`. You'll see
this prompt:

%%%gurk
>>> debug! 2 3 * 1 +
<-- ()
<-- (2 ())                                (:Put 2)
'next' or 'exit' (next):
%%%
As you can see, the first instruction already got executed.
Type in 'next' to go to the next step.
%%%gurk
<-- (3 (2 ()))                            (:Put 3)
'next' or 'exit' (next):
%%%

As you continue choosing 'next', you'll see the stack evolve as your
program gets executed.

Eventually, you'll see this prompt:

%%%gurk
<-- (1 (6 ()))                            (:CallByName '+')
'next' or 'exit' (next):
<-- (`+` (1 (6 ())))                      (:Put `+`)
'next' or 'exit' (next):
<-- (7 ())                                (:CallByValue)
'next' or 'exit' (next):
<-- (7 ())
accept the resulting state? y/n (n):
%%%

If you choose 'y', the new stack (`(7 ())`) will be used. Otherwise, the one
you started the debugger with will be restored.


## Syntax highlighting showcase

%%%gurk
:blah blah blah

#((
# Meh
"Hello, world" println
#))

:blah blah blah

#((good
# Hell yes!!!
(kittens (ducklings ())) hug
#))

:blah blah blah

#((bad
# DON'T EVER DO THIS!
"';--\n DROP TABLE users;" "INSERT INTO users VALUES {.};" format
#))
%%%
