/*
Definition:

{
    module: string,
    explanation: string,
    stackDiagram: string,
    aliases: string[]?,
}

*/

window.nameDefinitions = {
    "def": {
        module: "prelude",
        explanation: "Store *a value* by `name`",
        stackDiagram: "(value :name -- )",
    },
    "jar": {
        module: "prelude",
        explanation: "Store a function by name",
        stackDiagram: "(function :name -- )",
    },
    "+": {
        module: "math",
        explanation: "Add two integers",
        stackDiagram: "(m n -- m+n)",
    },
    "-": {
        module: "math",
        explanation: "Subtract one integer from another",
        stackDiagram: "(m n -- m-n)",
    },
    "*": {
        module: "math",
        explanation: "Multiply two integers",
        stackDiagram: "(m n -- m*n)",
    },
    "/": {
        module: "math",
        explanation: "Divide two integers, truncating the result",
        stackDiagram: "(m n -- m/n)",
    },
    "%": {
        module: "math",
        explanation: "Find the modulo of two integers",
        stackDiagram: "(m n -- m%n)",
    },
};