/*
Definition:

{
    module: string,
    explanation: string,
    stackDiagram: string,
    aliases: string[]?,
}

*/


window.nameDefinitions = {};


const addDefinitionsForModule = (module, definitions) => {
    for (const [name, definition] of Object.entries(definitions))
        Object.assign(
            window.nameDefinitions,
            {[name]: {module, ...definition}},
            {[module + "." + name]: {module, ...definition}},
        )
};


addDefinitionsForModule(
    "prelude",
    {
        "def": {
            explanation: "Store a value by name",
            stackDiagram: "(value :name -- )",
        },
        "jar": {
            explanation: "Store a function by name",
            stackDiagram: "(function :name -- )",
        },
        "import": {
            explanation: "Import a module. See the reference for all invocation modes.",
            stackDiagram: "(:module-name ? --)"
        },
        "println": {
            explanation: "Print a value and switch to a new line",
            stackDiagram: "(any -- )"
        },
        "print": {
            explanation: "Print a value without creating a new line",
            stackDiagram: "(any -- )"
        },
        "peek": {
            explanation: "Display the stack without changing it",
            stackDiagram: "( -- )"
        },
        "dup": {
            explanation: "Duplicate the element on top of the stack",
            stackDiagram: "(a -- a a)"
        },
        "drop": {
            explanation: "Discard the element on top of the stack",
            stackDiagram: "(a -- )"
        },
        "rot": {
            explanation: "See stack diagram",
            stackDiagram: "(a b c -- b c a)"
        },
        "unrot": {
            explanation: "inverse of `rot`",
            stackDiagram: "(a b c -- c a b)"
        },
    }
);


addDefinitionsForModule(
    "boxes",
    {
        "box": {
            explanation: "Create a box with a given initial value",
            stackDiagram: "(T -- box[T])",
        },
        "->": {
            explanation: "Read a stable value from a box",
            stackDiagram: "(box[T] -- T)",
        },
        "<-": {
            explanation: "Store a value into the box at the current transaction level",
            stackDiagram: "(box[T] T --)",
        },
        "-!>": {
            explanation: "Read a value into the box *at the current transaction level*",
            stackDiagram: "(box[T] -- T)",
        },
        "<=": {

            explanation: "Update a value in the box using a function",
            stackDiagram: "(box[T] (T -- T) --)",
        },
        "<[": {
            explanation: "Start a transaction for a box",
            stackDiagram: "(box[T] --)",
        },
        "]>": {
            explanation: "Commit and finish topmost transaction for a box",
            stackDiagram: "(box[T] --)",
        },
        "<<<": {
            explanation: "Roll back the topmost transaction for a box",
            stackDiagram: "(box[T] --)",
        },
    }
);


addDefinitionsForModule(
    "math",
    {
        "+": {
            explanation: "Add two integers",
            stackDiagram: "(m n -- m+n)",
        },
        "-": {
            explanation: "Subtract one integer from another",
            stackDiagram: "(m n -- m-n)",
        },
        "*": {
            explanation: "Multiply two integers",
            stackDiagram: "(m n -- m*n)",
        },
        "/": {
            explanation: "Divide two integers, truncating the result",
            stackDiagram: "(m n -- m/n)",
        },
        "%": {
            explanation: "Find the modulo of two integers",
            stackDiagram: "(m n -- m%n)",
        },
    }
)
