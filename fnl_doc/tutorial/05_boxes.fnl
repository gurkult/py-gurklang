($

((h 1) "Mutable variables with boxes")
(p
  "While immutable data is generally easier to understand and debug, sometimes
  you do want mutable state either for convenience or for performance.")
(p
  "And, admittedly, the real world is stateful. When you take a cookie of
  of a package, it's (unfortunately) not there anymore.")

((h 1) "Creating a box and reading from it")
(md
  "All values in Gurklang are immutable. You can't make a name first refer to
  something, and then make it refer to something else. However, you can make a name
  refer to a \"box\". Then you can retrive a value from the box or put a new value
  in, like in a file system or a database.

  Operations on boxes are located in the `boxes` standard module.

  To create a box, you need to call the `box` function with its initial value:")

(gurklang
  """
  :boxes ( box ) import

  # box (T -- box[T])
  0 box :my-box def
  """)

(p
  "You can read the value you've put in the box:")
(gurklang
  """
  :boxes ( box -> ) import

  0 box :my-box def

  # -> (box[T] -- T)
  my-box -> println  # 0
  """)

((h 1) "Writing to a box")
(p
  "The difference from a normal deifnition is that you can call the `<-` function
  to store something new in the box:")
(gurklang
  """
  :boxes ( box -> <- ) import

  0 box :my-box def

  box -> println  # 0

  # <- (box[T] T -- )
  my-box 5 <-

  my-box -> println  # 5
  """)

((h 1) "Applying a function to a box")
(p
  "If you wanted to change the value in the box using a function, you could do this:")
(gurklang
  """
  my-box my-box -> 2 + <-
  """)
(md
  "There's a shorthand for that, using the `<=` function:")
(gurklang
  """
  :boxes ( box -> <= ) import

  0 box :my-box def

  my-box -> println  # 0

  # <= (box[T] (T -- T) -- )
  my-box {2 +} <=

  my-box -> println  # 2
  """)

((h 1) "Example of boxes: REPL configuration")
(p
  "Try this in your REPL:")
(gurklang
  """
  >>> repl[prompt] ":-) " <-
  :-)
  :-) repl[prompt] ">>> " <-
  >>>
  >>>
  """)
(md
  "This is actually what styling functions like `repl[style:box]` do:")
(gurklang
  """
  {
    repl[ml-prompt]     "▋ "
    repl[prompt]        "│ "
    repl[before-output] "└───────────────────\n"
    repl[after-output]  ""
    repl[before-stack]  "├─"
    <- <- <- <- <-
  }
  :repl[style:box] jar
  """)

((h 1) "Advanced box usage: transactions")
(p
  "Suppose that you have a box that stores a list of even length:")
(gurklang
  """
  () box :list def
  """)

(md
  "...and you want to append two elements, `1` and `2` to it like this:")
(gurklang
  """
  list {:rest {1 rest},} <=
  list {:rest {2 rest},} <=
  """)
(p
  "...or maybe like this:")
(gurklang
  """
  { :x def {:rest def {x rest},} <= } :<-cons- jar

  list 1 <-cons-
  list 2 <-cons-
  """)

(md
  "But what if instead of `1` and `2` you want to push `1 f` and `:x :y g`?")
(gurklang
  """
  >>> list 1 f <-cons-
  >>> list :x :y g <-cons-
  #((bad
  Failure in function g:
  invariant violated: `list` is not of even length!
  #))
  """)

(md
  "What an unfortunate course of action. Turns out `g` relies on the list being
  of even length.

  For this to work, we'll need a _transaction_. A transaction allows you to
  work on a temporary copy of the box state and then save it.")

(gurklang
  """
  :boxes ( box -> <- <= <[ ]> ) import

  # <-cons- (box[list[T]] T --)
  { :x def
      {:rest def {x rest},} <=
  } :<-cons- jar

  () box :list def

  #((
  # <[ (box[_] --)
  list <[  # start the transaction

      list -> println  # ()

      list 1 <-cons-
      list -> println  # ()
      list 2 <-cons-
      list -> println  # ()

  # ]> (box[_] --)
  list ]>  # commit the result
  #))

  list -> println  # (2 (1 ()))
  # tada!
  """)

(md
  "You can use the `-!>` function to see the current active state of the box:")

(gurklang
  """
  list <[
      list 1 <-cons-
      list -!> println  # (1 ())
      list 2 <-cons-

  list ]>

  list -> println  # (2 (1 ()))
  """)

((h 1) "Inspecting box state")
(md
  "Sometimes you just want to see what's up with your boxes.

  `inspect` is a module which is similar to `inspect` and `ctypes` in
  Python. It provides reflection tools, as well as unholy hacks and dirty tricks.

  _Reflection_ is the ability to inspect some normally private information
  related to an object, for example, the name of a function.

  This is how you can see the current box state:")
(gurklang
  """
  >>> :inspect :prefix import
  >>> inspect.boxes!
  1 : ('... ' ())
  2 : ('>>> ' ())
  3 : ('' ())
  4 : ('' ())
  5 : ('<-- ' ())
  6 : (:false ())
  >>>
  """)

(p
  "This is how you can make a box given an ID:")
(gurklang
  """
  >>> 2 inspect.make-box! :b def
  >>> b -> peek drop
  ('>>> ' ())
  >>>
  """)

(p
  "This is how you can see the current state of a box:")
(gurklang
  """
  >>> 0 box :b def
  >>> b inspect.box-info!
  Box id: 7
  Box transactions: (0 ())
  >>> b <[
  >>> b 1 <-
  >>> b inspect.box-info!
  Box id: 7
  Box transactions: (1 (0 ()))
  >>> b 2 <-
  >>> b inspect.box-info!
  Box id: 7
  Box transactions: (2 (0 ()))
  >>> b <[
  >>> b 3 <-
  >>> b inspect.box-info!
  Box id: 7
  Box transactions: (3 (2 (0 ())))
  """)

((h 1) "Rollback")
(md
  "You can also _roll back_ a transaction, i.e. return it to its previous state.")
(gurklang
  """
  >>> b <<<  # rollback
  >>> b inspect.box-info!
  Box id: 7
  Box transactions: (2 (0 ()))
  >>> b ]>  # commit
  >>> b inspect.box-info!
  Box id: 7
  Box transactions: (2 ())
  """)

)
