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
        explanation: "Store a value by name",
        stackDiagram: "(value :name -- )",
    },
    "jar": {
        module: "prelude",
        explanation: "Store a function by name",
        stackDiagram: "(function :name -- )",
    },
    "import": {
        module: "prelude",
        explanation: "Import a module. See the reference for all invocation modes.",
        stackDiagram: "(:module-name ? --)"
    },
    "println": {
        module: "prelude",
        explanation: "Print a value and switch to a new line",
        stackDiagram: "(any --)"
    },
    "print": {
        module: "prelude",
        explanation: "Print a value without creating a new line",
        stackDiagram: "(any --)"
    },

    "box": {
        module: "boxes",
        explanation: "Create a box with a given initial value",
        stackDiagram: "(T -- box[T])",
    },
    "->": {
        module: "boxes",
        explanation: "Read a stable value from a box",
        stackDiagram: "(box[T] -- T)",
    },
    "<-": {
        module: "boxes",
        explanation: "Store a value into the box at the current transaction level",
        stackDiagram: "(box[T] T --)",
    },
    "-!>": {
        module: "boxes",
        explanation: "Read a value into the box *at the current transaction level*",
        stackDiagram: "(box[T] -- T)",
    },
    "<=": {
        module: "boxes",
        explanation: "Update a value in the box using a function",
        stackDiagram: "(box[T] (T -- T) --)",
    },
    "<[": {
        module: "boxes",
        explanation: "Start a transaction for a box",
        stackDiagram: "(box[T] --)",
    },
    "]>": {
        module: "boxes",
        explanation: "Commit and finish topmost transaction for a box",
        stackDiagram: "(box[T] --)",
    },
    "<<<": {
        module: "boxes",
        explanation: "Roll back the topmost transaction for a box",
        stackDiagram: "(box[T] --)",
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

for (const [name, definition] of {...window.nameDefinitions}) {
    window.nameDefinitions[`${definition.module}.${name}`] = definition;
}