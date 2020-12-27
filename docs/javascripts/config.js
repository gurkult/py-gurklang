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
    begin: /(?![:+-])[^\"'(){}# \n\t]+/,
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
