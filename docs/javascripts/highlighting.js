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
    begin: /(?!:|[+-]?\d)[^\"'(){}# \n\t]+/,
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
        class: 'meta',
        begin: /^\.\.\. /,
        end: '$',
        contains: DEFAULT_CONTAINS,
    }

    const replOnly = {
        class: 'meta',
        begin: '^>>> ',
        end: '$',
        contains: [...DEFAULT_CONTAINS, ellipsis],
    };

    return {
        name: 'Gurklang REPL',
        aliases: ['gurkrepl', 'gurklang-repl'],
        contains: [replOnly, gurklangError],
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

const attachTooltipToNode = node => {
    const name = node.textContent;
    const definition = window.nameDefinitions[name]
    if (definition) {
        const {module, explanation, stackDiagram} = definition;
        const parsedExplanation = parseDescription(escapeHtml(explanation));
        node.classList.add('tooltip');
        node.appendChild(htmlToElement(
              `<span class="tooltiptext">`
            + `<b>${module}.${name}</b> `
            + `<br/>${parsedExplanation}`
            + `<br/><tt>${escapeHtml(stackDiagram)}</tt>`
            + `</span>`
        ));
        console.log({name, definition});
    }
}

// wait until the definitions load, then attach them
const intervalId = setInterval(
    () => {
        if (!window.nameDefinitions)
            return;
        clearInterval(intervalId);
        document.querySelectorAll('.hljs-variable').forEach(attachTooltipToNode);
    },
    100
);