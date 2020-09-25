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
import {getTemplate as getNpFamilyMembers} from '../form/np-family-members';
import {SubmissionConsumer} from '../../data/submission';
import {FormConsumer} from '../../data/form';

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

        /** @type {FormConsumer} */
        this.formConsumer = new FormConsumer();

        /** @type {SubmissionConsumer} */
        this.submissionConsumer = new SubmissionConsumer();

        this.getContextData()
            .then(this.render.bind(this));
    }

    /**
     * Fetches requires data.
     * @return {Promise}
     */
    async getContextData() {
        const form = await this.formConsumer.read(this.node.dataset.formSlug)
            .catch(this.error.bind(this));

        const formStep = await form.readCurrentStep()
            .catch(this.error.bind(this));

        return {form, formStep};
    }

    /**
     * Gets called when Form.io form is ready.
     * @param {Form} form
     * @param {FormStep} formStep
     * @param {WebForm} webform
     */
    onFormReady(form, formStep, webform) {
        [...this.node.querySelectorAll('[type=submit]')]
            .forEach(this.bindButton.bind(this, webform));

        webform.on('submit', this.submitForm.bind(this, form, formStep));
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

    /**
     * Creates Submission and SubmissionStep for "form" "formStep".
     * @param {Form} form
     * @param {FormStep} formStep
     * @param {Object} formResult
     */
    submitForm(form, formStep, formResult) {
        const formData = formResult.data;

        this.submissionConsumer.create(form)
            .then(submission => submission.createSubmissionStep(formStep, formData))
            .then(this.submitFormSuccess.bind(this))
            .catch(this.error.bind(this));
    }

    submitFormSuccess(result) {
        console.info('Result', result);
    }

    /**
     * Generic error handler.
     * @param {*} error
     */
    error(error) {
        console.error(error);
        alert(error);
    }

    /**
     * Renders the form.
     * @param {Object} context
     */
    render(context) {
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

            // npFamilyMembers: {form: getNpFamilyMembers()},
        };

        Templates.OFLibrary = OFLibrary;
        Templates.current = Templates.OFLibrary;
        Formio.createForm(this.container, context.formStep.configuration)
            .then(this.onFormReady.bind(this, context.form, context.formStep));
    }
}


// Start!
[...FORMIO_FORMS].forEach(node => new FormIOForm(node));
