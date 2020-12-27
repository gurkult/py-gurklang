# Basic tutorial

Start by opening an interactive shell. First install git and python 3. 
Then install gurklang and open the interactive shell by entering the following into the command line
```sh
$ git clone https://github.com/gurkult/py-gurklang
$ cd py-gurklang
$ python -m pip install -r requirements.txt
$ python -m gurklang
```
(on some platforms, `python` will be `python3` or `py`)

you should see something like
```gurk
Gurklang v0.0.1
--------------
>>>
```
now you can enter commands for the gurklang runtime.
## The value stack

Gurklang uses a stack to store intermediate results.
You can think of a stack as a column of crates, with each new value going on top and all operations working from top to bottom. You start with no "crates". Lets add the first value (crate) to the stack.
enter `55` into the interactive shell
```gurk
>>> 55
>>>
```
it may seem like nothing happened, but this added the first value to the stack. The integer 55.
entering peek shows the current values on the stack. Lets put more numbers on and try it out
```gurk
>>> 44
>>> 11
>>> 0
>>> -9
>>> peek
(-9 (0 (11 (44 (55 ())))))
```
we can see that we have the numbers on the stack.
The topmost value of the stack is in the outermost parentheses. As we added -9 last, it is on top.
Lets say we want to remove the top value. For that we use `drop`.
```gurk
>>> drop
>>> peek
(0 (11 (44 (55 ()))))
```
You can also do multiple operations on the same line like so
```gurk
>>> drop drop 10 11 peek
(11 (10 (44 (55 ()))))
```
## Operations on the stack

in the future, we may want to look at the result of something without seeing the whole stack.
For this the `println` operation exists. It removes the top value from the stack and writes it to the shell
```gurk
>>> 20 println
20
>>>
```

Let's do some math. the `+` operation takes the top 2 numbers from the stack and adds them, then places the result on the stack.
```gurk
>>> peek + peek
(11 (10 (44 (55 ()))))
(21 (44 (55 ())))
```
10 and 11 are no longer on the stack, instead we get their sum, 21.
there is also `-` `/` `*`. `/` on integers always rounds down.

All mathematical expressions can be written this way, without parentheses. 
For example `(20 + 99) * (44 - 2 * 4 + 6)` will be written as. Try rewriting a few expressions yourself
```gurk
>>> 20 99 + 44 2 4 * - 6 + * println
```

there are also operations that manipulate the stack directly. We already saw one, `drop`.
There is also `dup` which takes the top value on the stack and leaves it on the stack twice.
```gurk
>>> 5 dup + println
10
```
`swap` will switch the top 2 element
```gurk
>>> 10 5 / println
2
>>> 10 5 swap / println
0
```

## Stack diagrams

Explaining the other stack manipulation operations verbally would be quite verbose, which is why we use so called stack diagrams. They are of the form
`(already on the stack topValue - left on the stack topValue)`
for example, `dup` looks like `( a - a a )` where `a` simply means any value. <details> <summary> Try to figure out how `drop` would look. </summary> `( a - )` </details>
with that explained, this is what the other operations look like
```gurk
swap  ( a b - b a )
over  ( a b - a b a )
rot   ( a b c - b c a )
unrot  ( a b c - c a b )
nip   ( a b - b )
tuck  ( a b - b a b )
```
<details> <summary> what will

```gurk
# rot is currently wrong, so this is not the actual result
1 2 3 4 rot + swap / swap dup + - println
```
result in

</summary>

`0`

</details>

## Other types of values on the stack

other than numbers, the stack can contain several other values
 - string, created with `'` or `"`, for example `"Hello World" println` will write Hello World to the shell.
 - atom, created with `:` followed by a valid name. `:atom`
 - functions, ...  
 - tuples, creates with `()` surrounding some other values. For example `(1 2 "A" b)`

## Custom Operations
quite often, you will find yourself needing to create your own operations. For this, there is the `jar` operation
