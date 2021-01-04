from ..builtin_utils import GurklangModule

module = GurklangModule(
name = "ds-pure",
exports = ["dict"],
source_code = R"""

{ :d jar :v1 def :k1 def
  { { (k2    :get) { k1 k2 = { v1 } { k2 :get d } if ! }
      (k2 v2 :set) { k2 v2 self dict-cons }
    } case
  } :self def
  self
} :dict-cons jar


{ { (_   :get) { :nil }
    (k v :set) { k v dict dict-cons }
  } case
} :dict def

""")
