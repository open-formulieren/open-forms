import {CrudConsumer, CrudConsumerObject} from 'consumerjs';


/**
 * A FormStep of a form.
 * @class
 */
class FormStep extends CrudConsumerObject {
    /**
     * Returns the URL for this Form.
     * @param {Form} form
     * @return {string}
     */
    getAbsoluteUrl(form) {
        const formUrl = form.getAbsoluteUrl();
        return `${formUrl}/${this.index}`;
    }
}


/**
 * Consumer used for CRUD operations on FormStep objects.
 * @class
 */
export class FormStepConsumer extends CrudConsumer {
    /**
     * Constructor method.
     */
    constructor() {
        super('/api/v1/forms/', FormStep);
    }

    /**
     * Reads all FormSteps from the backend for "form".
     * @param {Form} form The Form instance to create FormStep for.
     * @param {number} step The FormStep instance.
     * @return {Promise}
     */
    read(form, step) {
        return this.get(`${form.uuid}/steps/${step.uuid}`);
    }
}
