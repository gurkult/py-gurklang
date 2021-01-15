from ..builtin_utils import GurklangModule

module = GurklangModule(
name = "ds-pure",
exports = ["dict"],
source_code = R"""

{ :d jar :v1 def :k1 def
  { { (k2    :get) { k1 k2 = { v1 } { k2 :get d } if ! }
      (k2 v2 :set) { k2 v2 k1 k2 = d self if dict-cons }
      (k2    :del) { k2 v2 self dict- }
    } case
  } :self def
  self~
} :dict-cons jar


{ :d jar :k1
  { { (k2    :get) { k1 k2 = { :nil } { k2 :get d } if ! }
      (k2 v2 :set) { d v2 k2 k1 k2 = d self if dict-cons }
      (k2    :del) { k1 k2 = { self } { self k2 dict-del } if ! }
    } case
  } :self def
  self
} :dict-del jar


{ { (_   :get) { :nil }
    (k v :set) { k v dict dict-cons }
    (_   :del) { dict }
  } case
} :dict def

""")
