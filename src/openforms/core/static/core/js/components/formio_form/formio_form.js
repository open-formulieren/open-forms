import BEM from 'bem.js';
import {Formio} from 'formiojs';
import {BLOCK_FORMIO_FORM, ELEMENT_BODY, FORMIO_FORMS} from './constants';

/**
 * Renders a form.
 */
class FormIOForm {
    /**
     * Constructor method.
     * @param {HTMLElement} node
     */
    constructor(node) {
        /** @type {HTMLFormElement} */
        this.node = node;

        /** @type {HTMLElement} */
        this.container = BEM.getChildBEMNode(this.node, BLOCK_FORMIO_FORM, ELEMENT_BODY);

        this.render();
    }

    /**
     * Renders the form.
     */
    render() {
        const json = this.node.dataset.configuration;
        this.node.dataset.configuration = '';
        Formio.createForm(this.container, JSON.parse(json));
    }
}


// Start!
[...FORMIO_FORMS].forEach(node => new FormIOForm(node));
