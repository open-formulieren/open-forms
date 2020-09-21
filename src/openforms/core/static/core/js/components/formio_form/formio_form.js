import BEM from 'bem.js';
import {Formio} from 'formiojs';
import {BLOCK_FORMIO_FORM, ELEMENT_BODY, FORMIO_FORMS} from './constants';
import {FormDefinitionConsumer} from '../../data/form_definition';

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

        /** @type {FormDefinitionConsumer} */
        this.consumer = new FormDefinitionConsumer();

        this.getData();
    }

    /**
     * Fetches API data.
     * Calls render() on success.
     * Calls onError() on failure.
     */
    getData() {
        const url = this.node.dataset.schemeUrl;
        this.consumer.read(url)
            .then(this.render.bind(this))
            .catch(this.onError.bind(this))
        ;
    }

    /**
     * Updates this.container with error message.
     * Logs error to console.
     * @param error
     */
    onError(error) {
        this.container.innerText = error.statusText || error.message || 'Error';
        console.error(error);
    }

    /**
     * Renders the form.
     */
    render(formDefinition) {
        Formio.createForm(this.container, formDefinition);
    }
}


// Start!
[...FORMIO_FORMS].forEach(node => new FormIOForm(node));
