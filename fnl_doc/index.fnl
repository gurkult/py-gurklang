($

((h 1) "Welcome to the Gurklang documentation!")

(p "Gurklang is a"

  (list-unordered
    "stack-based"
    "dynamically typed"
    "functional")

  "programming language.")

((h 1) "What is...")

((h 2) "...'stack-based'?")

(md "In Gurklang, all operations manipulate a _stack_ in some way:")

(gurklang """
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
  >>>""")

(list-unordered
  (md "You start with a clean slate &mdash; an empty stack, denoted as `()`")
  (md "When you run the command `1`, you push the number `1` on top of the stack,
    and you end up with `(1 ())`, which means: `1`, then the empty stack.")
  (md "When you run the command `2`, you push the number `2` on top of the stack,
    and you end up with `(2 (1 ()))`, which means: `2`, then `1`, then the empty stack.")
  (md "Running `peek` simply prints the value of the stack")
)

(p
  "Creating numbers isn't very exciting. Let's destroy them!"
  (gurklang """
    >>> peek
    (4 (3 (2 (1 ()))))
    >>> drop
    >>> peek
    (3 (2 (1 ())))
    >>> drop drop
    >>> peek
    (1 ())""")
  (md "As you can see, `drop` simply discards the top value on the stack."))

(p
  (md "`dup`, on the other hand, duplicates the top value on the stack:")
  (gurklang """
    >>> peek
    (1 ())
    >>> dup peek
    (1 (1 ()))
    >>> dup peek
    (1 (1 (1 ())))"""))

(p
  "You can also do maths!"
  (gurklang """
    >>> peek
    (1 (1 (1 ())))
    >>> + peek
    (2 (1 ()))
    >>> + peek
    (3 ())
    >>> 14 peek
    (14 (3 ()))
    >>> * peek
    (42 ())""")
  (md
    "`+`, `*`, `-` pick the top two elements on the stack, do the respective
    operation on them, and put the result back on the stack."))

(p
  "Like in most programming languages, there are strings:"
  (gurklang """
    >>> 'Hello, world!'
    >>> peek
    ('Hello, world' ())
    >>> println
    Hello, world!
    >>> "Hello, world!" println
    Hello, world!""")
  "As you can see, both double and single quotes work.")

(p
  "If you're just tired of spelling out some value every time, you can define a name!"
  (gurklang """
    >>> 42 :answer def
    >>> "Hello, world!" :greeting def
    >>> answer peek
    (42 ())
    >>> greeting peek
    ('Hello, world' (42 ()))
    >>> drop drop"""))

(p
  "You can also define your own functions, which is the most important aspect of
  the language, but more on that later:"
  (gurklang """
    >>> { dup dup println println println } :3print jar
    >>>
    >>> "Hello," 3print "How low" println
    Hello,
    Hello,
    Hello,
    How low
    >>>"""))

((h 2) "...'dynamically typed'?")

(p "While each value has a fixed type (e.g. an integer, a string, a function),
type soundness is not statically determined.")

(p "On one hand, dynamic typing delays type errors until runtime:"
  (gurklang """
    >>> { dup + } :double jar
    >>> 5 double println
    10
    >>> "a" double println
    Failure in function +
    Reason: Str(value='a') cannot be added with Str(value='a')
    > Stack:  [1 2 3 4 a a]
    Type traceback? for complete Python traceback
    """))

(p
  "On the other hand, you get more flexibility. You can easily define a function
  that works on one type, two types, all types, or can even take a variable
  number of arguments from the stack.")

(p
  "Fun fact: a dynamically typed language will never reject a valid program!")

((h 2) "...'functional'?")

(p
  "Gurklang is influenced by functional programming languages, like Clojure and Haskell.
  Functional programming emphasizes:"

(list-unordered
  (b$ "Higher-order functions "(--)" functions that operate on functions"
    (gurklang """
      >>> 5 peek
      (5 ())
      >>> { 2 + }
      ({2 +} (5 ()))
      >>> !
      >>> peek
      (7 ())
      """)

    (gurklang """
      >>> { :f def  f ! f ! } :do-twice jar
      >>> 5
      >>> peek
      (5 ())
      >>> { 2 + } do-twice
      >>> peek
      (9 ())
      """))

  (b$ "Immutability: a definition is not a" (it " variable ") (--) "you can't reassign it."
    (gurklang """
      >>> 3 :pi def
      >>> 3 :e  def
      >>> 2 :e  def
      Failure in function def
      Reason: uncaught exception RuntimeError:
      Trying to reassign e
      > Stack:  [9 2 :e]
      RuntimeError: def uncaught exception RuntimeError:
      Trying to reassign e
      Type traceback? for complete Python traceback
      """)
      "There is a mechanism for managing mutable variables, but you'll rarely need it.")

  (b$
    "Expressive language and rich standard library"
    (gurklang """
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
      """))

  (b$
    "Strong typing: don't hide errors, bring them out!"
    (gurklang """
      >>> 1 2 =
      >>> println
      :false
      >>> 1 1 =
      >>> println
      :true
      >>> 1 "foo" =
      Failure in function =
      Reason: cannot compare type int with type str
      > Stack:  [9 1 foo]
      Type traceback? for complete Python traceback
      """))

  (b$
    "Great recursion support"
    (gurklang """
      >>> { dup 2 <
      ...   { drop 1 }
      ...   { dup 1 - n! * } parent-scope
      ...   if !
      ... } parent-scope :n! jar
      ...
      >>> 2000 n! println
      33162750924506332411753933805763240...
      >>>
      """))))
)
