import {CrudConsumer, CrudConsumerObject} from 'consumerjs';


/**
 * A FormStep of a form.
 * @class
 */
class FormStep extends CrudConsumerObject {
    /**
     * Returns the (frontend) URL for this FormStep.
     * @param {Form} form
     * @return {string}
     */
    getAbsoluteUrl(form) {
        const formUrl = form.getAbsoluteUrl();
        return `${formUrl}/${this.index + 1}`;  // index 2 human.
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
     * Reads a FormStep for form.
     * @param {Form} form The Form instance.
     * @param {string} stepUUID The FormStep uuid.
     * @return {Promise}
     */
    read(form, stepUUID) {
        return this.get(`${form.uuid}/steps/${stepUUID}`);
    }
}
