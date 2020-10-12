import {CrudConsumer, CrudConsumerObject} from 'consumerjs';


/**
 * A Submission of a form.
 * @class
 */
class Submission extends CrudConsumerObject {
    /**
     * Creates a SubmissionStep for this Submission.
     * @param {Form} form The Form instance.
     * @param {FormStep} formStep the FormStep instance.
     * @param {Object} formData
     * @return {Promise}
     */
    submit(form, formStep, formData) {
        return this.__consumer__.submit(form, formStep, formData);
    }
}


/**
 * Consumer used for CRUD operations on Submission objects.
 * @class
 */
export class SubmissionConsumer extends CrudConsumer {
    /**
     * Constructor method.
     */
    constructor() {
        super('/api/v1/form-submissions/', Submission);
    }

    /**
     * Will either create a new submission and save to the session, or retrieve an existing submission on the session,
     * or an existing submission for the form IF there is a BSN.
     * @param {Form} form The Form instance.
     * @return {Promise}
     */
    start(form) {
        return this.post(`${form.uuid}/start/`);
    }

    /**
     * Creates a SubmissionStep for this Submission.
     * @param {Form} form The Form instance.
     * @param {FormStep} formStep the FormStep instance.
     * @param {Object} formData
     * @return {Promise}
     */
    submit(form, formStep, formData) {
        return this.post(`${form.uuid}/submit/`, {
            form_step: formStep.url,
            data: formData,
        });
    }
}
