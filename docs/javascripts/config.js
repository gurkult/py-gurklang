
const plugin = hljs => {
    const number = {
        className: 'number',
        begin: /[+-]?\d+/,
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
        begin: /(?!:)[^\"'(){}# \n\t]+/,
    };

    const replPrompt = {
        className: 'built_in',
        begin: ">>>",
    };

    const vecLiteral = {
        punctuation,
        begin: /\(/,
        end: /\)/,
    };

    const codeLiteral = {
        punctuation,
        begin: /\{/,
        end: /\}/,
    };

    const comment = hljs.COMMENT('#', '$');

    const DEFAULT_CONTAINS = [
        replPrompt,
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

    return {
        name: 'Gurklang',
        aliases: ['gurk', 'gurklang'],
        contains: DEFAULT_CONTAINS,
    };
};
hljs.registerLanguage('gurklang', plugin);

hljs.initHighlighting();
