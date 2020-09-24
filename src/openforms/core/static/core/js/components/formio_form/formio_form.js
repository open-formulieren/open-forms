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
import {SubmissionConsumer} from '../../data/submission';

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

        /** @type {SubmissionConsumer} */
        this.submissionConsumer = new SubmissionConsumer();

        this.render();
    }

    /**
     * Gets called when Form.io form is ready.
     * @param {WebForm} webform
     */
    onFormReady(webform) {
        [...this.node.querySelectorAll('[type=submit]')]
            .forEach(this.bindButton.bind(this, webform));

        webform.on('submit', this.submitForm.bind(this));
    }

    /**
     * Binds "button" click to "webform" (Form.io instance)
     * @param webform
     * @param button
     */
    bindButton(webform, button) {
        button.addEventListener('click', this.onButtonClick.bind(this, webform));
    }

    /**
     * Gets called when any [type=submit] child of the of the form is pressed.
     * @param webform
     * @param event
     */
    onButtonClick(webform, event) {
        event.preventDefault();
        webform.submit();
    }

    submitForm(form) {
        const data = form.data;
        this.submissionConsumer.create({
            form: this.node.dataset.form,
            data
        }).then(s => console.info(s));
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
        Formio.createForm(this.container, JSON.parse(json))
            .then(this.onFormReady.bind(this));
    }
}


// Start!
[...FORMIO_FORMS].forEach(node => new FormIOForm(node));
