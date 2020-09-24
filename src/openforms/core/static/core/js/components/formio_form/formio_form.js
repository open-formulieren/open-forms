import BEM from 'bem.js';
import {Formio, Templates} from 'formiojs';
import {BLOCK_FORMIO_FORM, ELEMENT_BODY, FORMIO_FORMS} from './constants';
import {getTemplate as getComponent} from '../form/component';
import {getTemplate as getField} from '../form/field';
import {getTemplate as getLabel} from '../form/label';
import {getTemplate as getMessage} from '../form/message';
import {getTemplate as getButton} from '../form/button';
import {getTemplate as getText} from '../form/text';
import {getTemplate as getMultipleMasksInput} from '../form/multiple-masks-input';
import {getTemplate as getCheckbox} from '../form/checkbox';
import {getTemplate as getRadio} from '../form/radio';
import {getTemplate as getSelect} from '../form/select';

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
        const OFLibrary = {
            component: {form: getComponent()},
            field: {form: getField()},
            label: {form: getLabel()},
            message: {form: getMessage()},

            button: {form: getButton()},

            input: {form: getText()},
            multipleMasksInput: {form: getMultipleMasksInput()},

            checkbox: {form: getCheckbox()},
            radio: {form: getRadio()},

            select: {form: getSelect()},
        };

        Templates.OFLibrary = OFLibrary;
        Templates.current = Templates.OFLibrary;

        const json = this.node.dataset.configuration;
        this.node.dataset.configuration = '';

        console.log("render");
        Formio.createForm(this.container, JSON.parse(json));
    }
}


// Start!
[...FORMIO_FORMS].forEach(node => new FormIOForm(node));
