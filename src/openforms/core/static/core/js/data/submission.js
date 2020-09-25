import {CrudConsumer, CrudConsumerObject} from 'consumerjs';
import {SubmissionStepConsumer} from './submissionstep';


/**
 * A Submission of a form.
 * @class
 */
class Submission extends CrudConsumerObject {
    /**
     * Constructor method.
     */
    constructor(...args) {
        super(...args);
        this.submissionStepConsumer = new SubmissionStepConsumer();
    }

    /**
     * Creates a SubmissionStep for this Submission.
     * @param {FormStep} formStep
     * @param {Object} formData
     * @return {Promise}
     */
    createSubmissionStep(formStep, formData) {
        return this.submissionStepConsumer.create(this, formStep, formData);
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
        super('/api/v1/submissions/', Submission);
    }

    /**
     * Creates a SubmissionStep on the backend for "submission".
     * @param {Form} form The Form instance to create Submission for.
     * @return {Promise}
     */
    create(form) {
        return this.post('', {form: form.url});
    }
}
