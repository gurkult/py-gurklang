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
/**
 * @param node {Element}
 */
const displayTooltipOnTopOfEverything = node => {
    // keep track of whether the tooltip is shown
    // unattach the tooltip box from its original parent,
    // attach it to <body>, and move it to the right place
    const oldParent = node.parentElement;
    const newParent = document.querySelector("div#content");
    oldParent.removeChild(node);
    newParent.appendChild(node);
    node.style.position = "absolute";
    tooltipNodes.push(node);

    // when clicking on the original variable, toggle the tooltip
    node.style.visibility = 'hidden';
    oldParent.addEventListener('click', () => {
        tooltipNodes.forEach(n => {
            if (n !== node)
                n.style.visibility = 'hidden'
        });
        recalculatePosition();
        node.style.visibility = node.style.visibility === 'visible' ? 'hidden' : 'visible';
    });

    // we need to recalculate the coordinates when the window gets resized
    const recalculatePosition = () => {
        const {left, top} = oldParent.getBoundingClientRect();
        const {left: newParentLeft, top: newParentTop} = newParent.getBoundingClientRect();
        node.style.left = `${left - newParentLeft}px`;
        node.style.top = `${top - newParentTop + newParent.scrollTop + 24}px`;
    };
    window.addEventListener('resize', recalculatePosition);
};



/**
 * @param conditionFn { () => boolean }
 * @param stepMs { number= }
 */
const waitForCondition = (conditionFn, stepMs=100) =>
    new Promise((resolve, reject) => {
        const intervalId = setInterval(
            () => {
                if (conditionFn()){
                    clearInterval(intervalId);
                    resolve();
                }
            },
            stepMs
        );
    });


// wait until the definitions load, then attach them
window.fnl.onPageSwitch.push(async (title) => {
    console.log(`Gurklang: highlighting page ${title}`);
    await waitForCondition(() => window.nameDefinitions !== undefined);
    document.querySelectorAll('.gurklang--token--name').forEach(attachTooltipToNode);
    document.querySelectorAll('.tooltiptext').forEach(displayTooltipOnTopOfEverything)
});


window.fnl.onPageSwitch.push(async (title) => {
    console.log(`MathJax: typesetting ${title}`);
    await waitForCondition(() => window.MathJax.typeset !== undefined);
    window.MathJax.typeset();
});
