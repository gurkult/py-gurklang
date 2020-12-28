# Creating your own functions


```gurk
:math ( + - * / ) import

# comment
# TODO: Lorem ipsum dolor sit amet

42 :answer def

"Hello, world!" println

{ dup * swap dup * + }
:x*x+y*y jar

# Section comment:
#((

:math ( + - * / ) import

# comment
# TODO: Lorem ipsum dolor sit amet

42 :answer def

"Hello, world!" println

{ dup * swap dup * + }
:x*x+y*y jar

#))


```

```gurkrepl
>>> # REPL:
>>> 4 3 +
>>> peek
(7 ())
>>>
```
