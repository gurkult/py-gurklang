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


const tooltipNodes = [];
const displayTooltipOnTopOfEverything = node => {
    // keep track of whether the tooltip is shown
    // unattach the tooltip box from its original parent,
    // attach it to <body>, and move it to the right place
    const parent = node.parentElement;
    const {left, top} = parent.getBoundingClientRect();
    parent.removeChild(node);
    document.body.appendChild(node);
    node.style.position = "absolute";
    node.style.left = `${left}px`;
    node.style.top = `${top + scrollY + 24}px`;

    tooltipNodes.push(node);

    // when clicking on the original variable, toggle the tooltip
    node.style.visibility = 'hidden';
    parent.addEventListener('click', () => {
        tooltipNodes.forEach(n => {
            if (n !== node)
                n.style.visibility = 'hidden'
        });
        recalculatePosition();
        node.style.visibility = node.style.visibility === 'visible' ? 'hidden' : 'visible';
    });

    // we need to recalculate the coordinates when the window gets resized
    const recalculatePosition = () => {
        const {left, top} = parent.getBoundingClientRect();
        node.style.left = `${left}px`;
        node.style.top = `${top + scrollY + 24}px`;
    };
    window.addEventListener('resize', recalculatePosition);
};


// wait until the definitions load, then attach them
const intervalId = setInterval(
    () => {
        if (!window.nameDefinitions)
            return;
        clearInterval(intervalId);
        document.querySelectorAll('.gurklang--token--name').forEach(attachTooltipToNode);
        document.querySelectorAll('.tooltiptext').forEach(displayTooltipOnTopOfEverything)
    },
    100
);
