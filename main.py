import pprint
import gurklang.vm as vm
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

stack, scope = vm.run(parse(source3))

print("\n----------------")
print("Resulting stack:")
pprint.pprint(vm.repr_stack(stack))