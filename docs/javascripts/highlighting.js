const number = {
    className: 'number',
    begin: /[+-]?\d+(?=[(){}"'#]| |\n|$)/,
};

const doubleQuotedString = {
    className: 'string',
    begin: '"', end: '"',
    contains: [{begin: '\\\\.'}],
};

const singleQuotedString = {
    className: 'string',
    begin: "'", end: "'",
    contains: [{begin: '\\\\.'}],
};

const atom = {
    className: 'symbol',
    begin: /:[^\"'(){}# \n\t]+/,
};

const identifier = {
    className: 'variable',
    begin: /(?!:|[+-]?\d(?:[\"'(){}# \n\t]|$))[^\"'(){}# \n\t]+/,
};

const replPrompt = {
    className: 'meta',
    begin: ">>> ",
    relevance: 10,
};

const vecLiteral = {
    className: 'punctuation hljs-gurklang-list',
    begin: /\(/,
    end: /\)/,
};

const codeLiteral = {
    className: 'punctuation hljs-gurklang-code',
    begin: /\{/,
    end: /\}/,
};

const sectionComment = {
    className: 'section-comment',
    begin: /#\(\(/,
    end: /#\)\)/,
};

const comment = hljs.COMMENT('#[^)][^)]', '$');

const DEFAULT_CONTAINS = [
    sectionComment,
    comment,
    number,
    atom,
    identifier,
    singleQuotedString,
    doubleQuotedString,
    vecLiteral,
    codeLiteral,
];

vecLiteral.contains = DEFAULT_CONTAINS;
codeLiteral.contains = DEFAULT_CONTAINS;
sectionComment.contains = DEFAULT_CONTAINS;


const gurklang = hljs => {
    return {
        name: 'Gurklang',
        aliases: ['gurk', 'gurklang'],
        contains: [replPrompt, ...DEFAULT_CONTAINS],
    };
};
hljs.registerLanguage('gurklang', gurklang);



const gurklangError = {
    className: 'deletion',
    begin: 'Failure in function',
    end: 'Type traceback\? for complete Python traceback',
};


const gurklangRepl = hljs => {
    const ellipsis = {
        className: 'meta',
        begin: /^\.\.\. /,
        end: '$',
        contains: DEFAULT_CONTAINS,
    }

    const replOnly = {
        className: 'meta',
        begin: '^>>>',
        end: '$',
        contains: [ellipsis, ...DEFAULT_CONTAINS],
    };

    return {
        name: 'Gurklang REPL',
        aliases: ['gurkrepl', 'gurklang-repl'],
        contains: [replOnly, ellipsis, gurklangError],
    };
};
hljs.registerLanguage('gurklang-repl', gurklangRepl);


hljs.initHighlighting();


/// Tooltip stuff:
// TODO: REFACTOR

const htmlToElement = html => {
    const template = document.createElement('template');
    template.innerHTML = html.trim();
    return template.content.firstChild;
};

const partialReduce = (a, f) => x => a.reduce(f, x);

const replacer = (...replacements) => string => replacements.reduce(
    (acc, [pattern, replacement]) => acc.replace(pattern, replacement),
    string
);


const escapeHtml = replacer(
    [/&/g, "&amp;"],
    [/</g, "&lt;"],
    [/>/g, "&gt;"],
    [/"/g, "&quot;"],
    [/'/g, "&#039;"]
);

const parseDescription = replacer(
    [/\*(?:[^*]|\\\*)+\*/g, m => `<i>${m.slice(1, -1)}</i>`],
    [/`(?:[^`]|\\\`)+`/g, m => `<tt>${m.slice(1, -1)}</tt>`],
);


/////////////////////////////////////////////
// DOM manipulations                       //
// Lasciate ogni speranza, voi ch'entrate  //
/////////////////////////////////////////////

const attachTooltipToNode = node => {
    const name = node.textContent;
    const definition = window.nameDefinitions[name]
    if (!definition)
        return;
    const {module, explanation, stackDiagram} = definition;
    const parsedExplanation = parseDescription(escapeHtml(explanation));
    node.classList.add('tooltip');
    const qualifiedName = module === "prelude" ? name : `${module}.${name}`;
    node.appendChild(htmlToElement(
            `<div class="tooltiptext docs-tooltip">`
        + `    <div class="docs-tooltip-title">`
        + `        ${escapeHtml(qualifiedName)}`
        + `    </div>`
        + `    <div class="docs-tooltip-explanation">`
        + `        ${parsedExplanation}`
        + `    </div>`
        + `    <div class="docs-tooltip-stack-diagram">`
        + `        ${escapeHtml(stackDiagram)}`
        + `    </div>`
        + `</div>`
    ));
}


const displayTooltipOnTopOfEverything = node => {
    // keep track of whether the tooltip is shown
    let show = false;

    // unattach the tooltip box from its original parent,
    // attach it to <body>, and move it to the right place
    const parent = node.parentElement;
    const {left, top} = parent.getBoundingClientRect();
    parent.removeChild(node);
    document.body.appendChild(node);
    node.style.position = "absolute";
    node.style.left = `${left}px`;
    node.style.top = `${top + scrollY + 24}px`;

    // when clicking on the original variable, toggle the tooltip
    node.style.visibility = 'hidden';
    parent.addEventListener('click', () => {
        show = !show;
        node.style.visibility = show ? 'visible' : 'hidden';
    });

    // we need to recalculate the coordinates when the window gets resized
    const onResize = () => {
        const {left, top} = parent.getBoundingClientRect();
        node.style.left = `${left + 32}px`;
        node.style.top = `${top + scrollY}px`;
    };
    window.addEventListener('resize', onResize);
};


// wait until the definitions load, then attach them
const intervalId = setInterval(
    () => {
        if (!window.nameDefinitions)
            return;
        clearInterval(intervalId);
        document.querySelectorAll('.hljs-variable').forEach(attachTooltipToNode);
        document.querySelectorAll('.tooltiptext').forEach(displayTooltipOnTopOfEverything)
    },
    100
);
