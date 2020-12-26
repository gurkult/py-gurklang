DEFAULT_PRELUDE = R"""
:repl-utils :all                               import
:inspect    :prefix                            import
:coro       :prefix                            import
:math       ( < + - * / % %make %+ %- %* %/ )  import
:boxes      ( box <- -> )                      import


"" box :repl[ml-prompt]     var
"" box :repl[prompt]        var
"" box :repl[before-output] var
"" box :repl[after-output]  var
"" box :repl[before-stack]  var


{
  repl[ml-prompt]     "... "
  repl[prompt]        ">>> "
  repl[before-output] ""
  repl[after-output]  ""
  repl[before-stack]  "<-- "
  <- <- <- <- <-
}
:repl[style:default] jar


{
  repl[ml-prompt]     "▋ "
  repl[prompt]        "│ "
  repl[before-output] "└───────────────────\n"
  repl[after-output]  ""
  repl[before-stack]  "├─"
  <- <- <- <- <-
}
:repl[style:box] jar


{
  repl[ml-prompt]     "▋ "
  repl[prompt]        "│\n│ "
  repl[before-output] "└───────────────────\n"
  repl[after-output]  "\n"
  repl[before-stack]  "│\n╞═"
  <- <- <- <- <-
}
:repl[style:box-wide] jar


{
  repl[ml-prompt]     "│ "
  repl[prompt]        "In:\n  "
  repl[before-output] "Out:\n  "
  repl[after-output]  "\n"
  repl[before-stack]  "Stack:\n  "
  <- <- <- <-
}
:repl[style:in-out] jar


:false box :repl[display-stack] var

{ repl[display-stack] :true <- }
:show-stack jar

{ repl[display-stack] :false <- }
:hide-stack jar


repl[style:default]
hide-stack


"Gurklang v0.0.1" println
"---------------" println
"""

BACKSLASH_MAPPING = {
    "lambda": "λ",
    "le": "≤",
    "ge": "≥",
    "empty-set": "∅",
    "in": "∈",
    "not-in": "∉",
    "sub": "⊂",
    "nsub": "⊄",
    "sube": "⊂",
    "union": "∪",
    "inters": "∩",
    "nsube": "⊈",
    "ne": "≠",
    "approx": "≈",
    "compose": "∘",
    "forall": "∀",
    "exists": "∃",
    "not": "¬",
    "or": "∨",
    "and": "∧",
    "rarr": "→",
    "larr": "←",
    "T": "⊤",
    "F": "⊥",
}
