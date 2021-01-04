window.MathJax = {
    skipStartupTypeset: true,
    tex: {
        inlineMath: [["$", "$"]],
        displayMath: [["!!", "!!"]],
        processEscapes: true,
        processEnvironments: true
    },
    options: {
        ignoreHtmlClass: ".*|",
        processHtmlClass: "math-inline|math-display"
    },
    svg: {
        fontCache: 'global'
    }
};

(() => {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    script.async = true;
    document.head.appendChild(script);
})();
