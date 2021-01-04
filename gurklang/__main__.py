import sys
from . import repl, vm, parser

args = sys.argv[1:]

if args == []:
    repl.repl()
elif args == ["-i"]:
    source = sys.stdin.read()
    parsed = parser.parse(source)
    vm.run(parsed)
elif args[0] == "-r":
    filename = args[1]
    with open(filename) as source_file:
        source = source_file.read()
    repl.run_and_open_repl(source)
elif len(args) == 1:
    filename = args[0]
    with open(filename) as source_file:
        source = source_file.read()
    parsed = parser.parse(source)
    vm.run(parsed)
elif args[0] == "-c":
    source = " ".join(args[1:])
    parsed = parser.parse(source)
    vm.run(parsed)
else:
    print("Invalid arguments. Valid execution modes:")
    print("gurklang : open the REPL")
    print("gurklang path/to/file : run a program from file")
    print("gurklang -r path/to/file : run a program from file and open the REPL")
    print("gurklang -c 'program' : run a program specified in the arguments after `-c`")
    print("gurklang -i : run a program read from the standard input")
