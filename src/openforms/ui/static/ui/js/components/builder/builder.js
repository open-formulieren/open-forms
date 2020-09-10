// jshint ignore: start
import BEM from 'bem.js';
import {Formio, Components} from 'formiojs';

import {BLOCK_FORM_BUILDER, ELEMENT_CONTAINER, INPUT_ELEMENT} from '../constants';


/**
 * Installs Form.io on ELEMENT_CONTAINER.
 * @class
 */
class FormIOBuilder {
    /**
     * Constructor method.
     * @param {HTMLElement} node
     */
    constructor(node) {
        /** @type {HTMLElement} */
        this.node = node;

        /** @type {HTMLElement} */
        this.container = BEM.getChildBEMNode(this.node, BLOCK_FORM_BUILDER, ELEMENT_CONTAINER);

        /** @type {string} */
        this.configurationInput = BEM.getChildBEMNode(this.node, BLOCK_FORM_BUILDER, INPUT_ELEMENT);

        this.configuration = {};
        if (this.configurationInput.value) {
            this.configuration = JSON.parse(this.configurationInput.value);
        }

        this.render();
    }

    /**
     * Mounts Form.io
     */
    render() {
        Formio.builder(this.container, this.configuration, {
            builder: {
                basic: false,
                advanced: false,
                data: false,
                layout: false,
                premium: false,

                customBasic: {
                    title: 'Components',
                    default: true,
                    components: {
                        textfield: true,
                    }
                }
            },
        })
            .then(form => {
                form.on('change', formObj => {
                    this.configurationInput.setAttribute('value', JSON.stringify(formObj));
                });
            });
    }
}

document.addEventListener("DOMContentLoaded", event => {
    const FORM_BUILDERS = BEM.getBEMNodes(BLOCK_FORM_BUILDER);
    [...FORM_BUILDERS].forEach(node => {
        new FormIOBuilder(node);
    });
});

