# Mutable variables with `boxes`

While immutable data is generally easier to understand and debug, sometimes
you do want mutable state either for convenience or for performance.

And, admittedly, the real world is stateful. When you take a cookie of
of a package, it's (unfortunately) not there anymore.

# Creating a box and reading from it

All values in Gurklang are immutable. You can't make a name first refer to
something, and then make it refer to something else. However, you can make a name
refer to a "box". Then you can retrive a value from the box or put a new value
in, like in a file system or a database.

Operations on boxes are located in the `boxes` standard module.

To create a box, you need to call the `box` function with its initial value:

```gurk
:boxes ( box ) import

0 box :my-box var
```


Now you can read