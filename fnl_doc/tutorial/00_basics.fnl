($
((h 1) "Basic tutorial")

(p
"
Start by opening an interactive shell. First install git and python 3.
Then install gurklang and open the interactive shell by entering the following into the command line
")
(gurklang
"""
$ git clone https://github.com/gurkult/py-gurklang
$ cd py-gurklang
$ python -m pip install -r requirements.txt
$ python -m gurklang
"""
)
(md "on some platforms, `python` will be `python3` or `py`")
(p "you should see something like")
(gurklang
"""
Gurklang v0.0.1
--------------
>>>
""")
(p "now you can enter commands for the gurklang runtime.")
((h 2) "The Value Stack")

(md
"
Gurklang uses a stack to store intermediate results.
You can think of a stack as a column of crates, with each new value going on top and all operations working from top to bottom. You start with no 'crates'. Lets add the first value (crate) to the stack.
enter `55` into the interactive shell
")
(gurklang
"""
>>> 55
>>>
""")
(p
"
it may seem like nothing happened, but this added the first value to the stack. The integer 55.
entering peek shows the current values on the stack. Lets put more numbers on and try it out
"
(gurklang
"""
>>> 44
>>> 11
>>> 0
>>> -9
>>> peek
(-9 (0 (11 (44 (55 ())))))
""")
(md "
we can see that we have the numbers on the stack.
The topmost value of the stack is in the outermost parentheses. As we added -9 last, it is on top.
Lets say we want to remove the top value. For that we use the function `drop`.
")
(gurklang
"""
>>> drop
>>> peek
(0 (11 (44 (55 ()))))
""")
(p "You can also call multiple functions on the same line like so")
(gurklang
"""
>>> drop drop 10 11 peek
(11 (10 (44 (55 ()))))
""")
((h 2) "Reading from the stack")

(md "in the future, we may want to look at the result of something without seeing the whole stack.
For this the `println` function exists. It removes the top value from the stack and writes it to the shell")
(gurklang
"""
>>> 20 println
20
>>>
""")

(md "Let's do some math. the `+` function takes the top 2 numbers from the stack and adds them, then places the result on the stack.
")
(gurklang
"""
>>> peek + peek
(11 (10 (44 (55 ()))))
(21 (44 (55 ())))
""")
(md "
10 and 11 are no longer on the stack, instead we get their sum, 21.
there is also `-` `/` `*`. `/` on integers always rounds down.

All mathematical expressions can be written this way, without parentheses. 
For example `(20 + 99) * (44 - 2 * 4 + 6)` will be written as.
")
(gurklang
"""
20 99 + 44 2 4 * - 6 + *
""")

(p "Try rewriting a few expressions yourself.")

(tt "1 + 2 * 3 + 4 / 5")
(adm &answer
    (gurklang """
    1 2 3 * 4 5 / + +
    """))

(tt "(1 + 2) * (3 + 4) / 5")
(adm &answer
    (gurklang """
    1 2 + 3 4 + * 5 /
    """))

(md "there are also operations that manipulate the stack directly. We already saw one, `drop`.
There is also `dup` which takes the top value on the stack and leaves it on the stack twice.
")

(gurklang
"""
>>> 5 dup + println
10
""")
 
(md "`swap` will switch the top 2 element")

(gurklang
"""
>>> 10 5 / println
2
>>> 10 5 swap / println
0
""")

((h 2) "Stack diagrams")

(md "Explaining the other stack manipulation operations verbally would be quite verbose, which is why we use so called stack diagrams. They are of the form
`(already on the stack topValue - left on the stack topValue)`
for example, `dup` looks like `( a - a a )` where `a` simply means any value. Try to figure out how `drop` would look like.")

(adm &answer  (tt "( a - )"))

(p "with that explained, this is what the other operations look like")

(gurklang
"""
swap  ( a b - b a )
over  ( a b - a b a )
rot   ( a b c - b c a )
unrot  ( a b c - c a b )
nip   ( a b - b )
tuck  ( a b - b a b )
""")

(p "what will")

(gurklang
"""
1 2 3 4 rot + swap / swap dup + - println
""")

(p "result in")
(adm &answer (tt "0"))
((h 2) "Other types of values on the stack")

(p "other than numbers, the stack can contain several other values")
(list-unordered
 (md "string, created with quote surrounded text")
 (md "atom, created with `:` followed by a valid name. `:atom`")
 (md "tuples, creates with `()` surrounding some other values. For example `(1 2 'A' b)`")
 (md "functions, created with `{}`, see the functions tutorial for more details"))
))
