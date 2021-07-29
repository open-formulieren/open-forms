import copy from 'copy-to-clipboard';

const SELECTOR = '.sdk-snippet';


/**
 * Bind click event on copy icon to copy the snippet content.
 * @param  {DOMNode} node The sdk-snippet component.
 * @return {Void}
 */
const enableSnippetCopy = (node) => {
    const icon = node.querySelector(`${SELECTOR}__copy`);
    icon.addEventListener('click', (event) => {
        event.preventDefault();
        const snippet = node.querySelector(`${SELECTOR}__snippet`);
        copy(snippet.textContent, {format: 'text/plain'});

        // change the icon to indicate it was copied
        const faIcon = icon.querySelector('.fa');
        faIcon.classList.replace("fa-clone", "fa-check");
        setTimeout(() => {
            faIcon.classList.replace("fa-check", "fa-clone");
        }, 500);
    });
};

const nodes = document.querySelectorAll(SELECTOR);
for (const node of nodes) {
    enableSnippetCopy(node);
}
