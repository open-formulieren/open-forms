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
import {FormConsumer} from '../../data/form';

/**
 * Renders a form.
 */
export class FormIOForm {
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

        /** @type {Object} */
        this.webForm = {};

        this.configureTemplates();
        this.bindEvents();

        this.getContextData()
            .then(this.mount.bind(this))
            .then(this.render.bind(this))
            .catch(this.error.bind(this))
        ;
    }

    /**
     * Binds events to callbacks.
     */
    bindEvents() {
        window.addEventListener('popstate', (event) => {
            this.render(event.state);
        });
    }

    /**
     * Binds "button" click to "webform" (Form.io instance)
     * @param button
     */
    bindButton(button) {
        button.addEventListener('click', this.onButtonClick.bind(this));
    }

    /**
     * Returns the step index for "form" based on URL or null if not found.
     * @return {(number|null)}
     */
    getStep(form, submission) {
        try {
            const index = parseInt(
                String(window.location.pathname).match(/(\d+)\/?$/)[1]  // Number(s) at end of the url.
            );
            return form.steps[index - 1];
        } catch (e) {
            return null;
        }
    }

    /**
     * Gets called when any [type=submit] child of the of the form is pressed.
     * @param event
     */
    onButtonClick(event) {
        event.preventDefault();
        this.webForm.submit();
    }

    /**
     * Gets called when Form.io form is ready.
     * @param {Object} context
     */
    onFormReady(context) {
        [...this.node.querySelectorAll('[type=submit]')]
            .forEach(this.bindButton.bind(this));

        this.webForm.on('submit', this.submitForm.bind(this, context));
    }

    /**
     * Creates Submission and SubmissionStep for "form" "formStep".
     * @param {Object} context
     * @param {Object} formResult
     */
    submitForm(context, formResult) {
        const {form, formStep, submission} = context;
        const formData = formResult.data;

        submission.createSubmissionStep(formStep, formData)
            .then(this.submitFormSuccess.bind(this, form))
            .catch(this.error.bind(this));
    }

    /**
     * Gets called when Submission and SubmissionStep have been sucessfully created.
     */
    submitFormSuccess() {
        this.getContextData(true)
            .then(this.render.bind(this))
            .catch(this.error.bind(this))
        ;
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
     * Configures the (custom) Form.io templates.
     */
    configureTemplates() {
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
    }

    /**
     * Loads context data.
     * @param {boolean} [next=false] Whether to load the next step.
     * @return {Promise}
     */
    async getContextData(next = false) {
        // Fetch data.
        const form = await this.formConsumer.read(this.node.dataset.formId);
        const submission = await this.submissionConsumer.create(form);
        const stepIndex = next === false ? this.getStep(form, submission) : null;  // Null value causes FormConsumer to read user_current_step.
        const formStep = await form.readCurrentStep(stepIndex);

        // Update history with received context.
        const formState = JSON.parse(form.asJSON());
        const formStepState = JSON.parse(formStep.asJSON());
        const submissionState = JSON.parse(submission.asJSON());

        const formStepUrl = formStep.getAbsoluteUrl(form);
        console.log(formStepUrl);

        history.pushState({
            form: formState,
            formStep: formStepState,
            submission: submissionState
        }, document.title, formStepUrl);

        // Return context.
        return {form, formStep, submission};
    }

    /**
     * Creates an empty Form.io form, sets this.webForm and calls onFormReady() and render() when done.
     * @param context
     * @return {Promise}
     */
    mount(context) {
        return Formio.createForm(this.container, {})
            .then(webForm => {
                this.webForm = webForm;
                this.onFormReady(context);
                return context;
            });
    }

    /**
     * Renders the form configuration on this.webForm.
     * @param {Object} context
     */
    render(context) {
        // Renders is called as side effect of "popstate" event, hence context may be empty.
        if (!context) {
            return;
        }

        // Fixme: this seems to happen in tests, unclear why.
        if (!this.webForm.setForm) {
            return;
        }

        const {formStep} = context;
        this.webForm.setForm(formStep.configuration);
    }
}


// Start!
[...FORMIO_FORMS].forEach(node => new FormIOForm(node));
