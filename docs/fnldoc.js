(() => { // <IIFE>

/**
 * @param name {string}
 * @param htmlContent {string}
 * @param contentSetter {string => void}
 */
const createTocLeaf = (name, htmlContent, contentSetter) => {
    const li = document.createElement("li");
    li.setAttribute("class", "fnldoc--toc--point fnldoc--toc--leaf");

    const link = document.createElement("a");
    link.href = "#";
    link.innerText = name
    link.addEventListener("click", () => {
        contentSetter(name, htmlContent);
    });
    li.appendChild(link);
    return li;
}

/**
 * @param name {string}
 * @param content {Record<string, any>}
 * @param contentSetter {string => void}
 */
const createTocBranch = (name, content, contentSetter) => {
    const li = document.createElement("li");
    li.setAttribute("class", "fnldoc--toc--point fnldoc--toc--node");

    const span = document.createElement("span");
    span.setAttribute("class", "fnldoc--toc--branch-label");
    span.innerText = name + " ";

    const toggleBranch = () => {
        toggleButton.classList.toggle("--open");
        nav.classList.toggle("--hidden");
    };

    const toggleButton = document.createElement("button");
    toggleButton.setAttribute("class", "fnldoc--toc--toggle")
    span.addEventListener("click", toggleBranch);
    toggleButton.addEventListener("click", toggleBranch);
    li.appendChild(span);
    li.appendChild(toggleButton);

    const nav = document.createElement("nav");
    nav.appendChild(tocToBulletList(content, contentSetter));
    nav.classList.add("fnldoc--toc--nested");
    nav.classList.add("--hidden");

    li.appendChild(nav);
    return li;
}

/**
 * @param toc {Record<string, any>}
 * @param contentSetter {string => void}
 */
const tocToBulletList = (toc, contentSetter) => {
    const list = document.createElement("ul");
    for (const [name, content] of Object.entries(toc))
        if (typeof content === "string")
            list.appendChild(createTocLeaf(name, content, contentSetter));
        else
            list.appendChild(createTocBranch(name, content, contentSetter));
    return list;
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


/**
 * @param {{
 *      toc: Element,
 *      main: Element,
 *      title: Element,
 * }}
 */
window.loadFnlDoc = async ({toc, main, title}) => {
    await waitForCondition(() => window.fnl !== undefined);

    /**
     * @param titleText {string}
     * @param htmlContent {string}
     */
    const contentSetter = (titleText, htmlContent) => {
        window.fnl.onPageSwitch.forEach(fn => fn(titleText));
        title.innerHTML = titleText;
        main.innerHTML = htmlContent;
    };

    const {compiledHtml} = window.fnl;
    const element = tocToBulletList(compiledHtml, contentSetter);
    toc.appendChild(element);

    contentSetter(window.fnl.start, compiledHtml[window.fnl.start]);
};

})(); // </IIFE>
