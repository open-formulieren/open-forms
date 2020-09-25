import {CrudConsumer, CrudConsumerObject} from 'consumerjs';


/**
 * A SubmissionStep of a form.
 * @class
 */
class SubmissionStep extends CrudConsumerObject {
}


/**
 * Consumer used for CRUD operations on SubmissionStep objects.
 * @class
 */
export class SubmissionStepConsumer extends CrudConsumer {
    /**
     * Constructor method.
     */
    constructor() {
        super('/api/v1/submission/', SubmissionStep);
    }

    /**
     * Creates a SubmissionStep on the backend for "submission".
     * @param {Submission} submission The Submission instance to create SubmissionStep for.
     * @param {FormStep} formStep The FormStep to create SubmissionStep for.
     * @param formData {Object} Key/value object containing the form data to store.
     * @return {Promise}
     */
    create(submission, formStep, formData) {
        return this.post(`${submission.url}steps/`, {
            form_step: `${submission.form}steps/${formStep.index}/`,  // FIXME
            data: formData
        });
    }

    /**
     * Reads all SubmissionSteps from the backend for "submission".
     * @param {Submission} submission The Submission instance to create SubmissionStep for.
     * @return {Promise}
     */
    read(submission) {
        return this.get(`${submission.url}steps`);
    }
}
