import pprint
import gurklang.vm as vm
from gurklang.vm_utils import repr_stack
from gurklang.parser import parse


source1 = R"""
{ :b var :a var b a } :my_swap jar
1 2 3 4 my_swap
"""

source2 = R"""
{ :x var { x + } } :make_adder jar
5 make_adder :add5 jar

"Answer:" print
37 add5 print
37 { add5 } ! print
"""

source3 = R"""
{1} {2} :true if print

{1} {2} :false if print
"""

source4 = r"""
:math :qual import

160 15 :%make math   # 160 15 %make      ~  (32 3)
4 10 :%make math     # 4 10 %make        ~  (2 5)
:%+ math print       # (23 3) (4 10) %+  ~  (166 15)
"""


source5 = r"""
# 1. Only import certain names (from math import %make)
:math (%make) import
4 2 %make print

# 2. Import all the names (from math import *)
:math :all import
4 2 %make print

# 3. Qualified import (import math)
:math :qual import
4 2 :%make math print

# 4. Renaming qualified import (import math as shmath)
:math :as:shmath import
4 2 :%make shmath print

# 5. Prefixed import (from math import * as "math_*")
:math :prefix import
4 2 math.%make print

# 6. Custom prefixed import (from math import * as "math_*")
:math :prefix:shmath import
4 2 shmath.%make print
"""


source6 = R"""
:math ( + ) import

{ { + } close } :make-adder jar

5 make-adder :add5 jar

37 add5 print  #=> 42
40 add5 print  #=> 45
"""

stack, scope = vm.run(parse(source6))

print("\n----------------")
print("Resulting stack:")
pprint.pprint(repr_stack(stack))