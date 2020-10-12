import {CrudConsumer, CrudConsumerObject} from 'consumerjs';
import {FormStepConsumer} from './formstep';


/**
 * A Form.
 * @class
 */
class Form extends CrudConsumerObject {
    /**
     * Constructor method.
     */
    constructor(...args) {
        super(...args);
        this.formStepConsumer = new FormStepConsumer();
    }

    /**
     * Returns the (frontend) URL for this Form.
     * @return {string}
     */
    getAbsoluteUrl() {
        return `/${this.slug}`;
    }

    /**
     * Reads a FormStep for this Form.
     * @param {number} stepUUID The uuid of the step to load.
     * @return {Promise}
     */
    readStep(stepUUID) {
        return this.formStepConsumer.read(this, stepUUID);
    }
}


/**
 * Consumer used for CRUD operations on Form objects.
 * @class
 */
export class FormConsumer extends CrudConsumer {
    /**
     * Constructor method.
     */
    constructor() {
        super('/api/v1/forms/', Form);

        this.unserializableFields = [...this.unserializableFields, 'formStepConsumer'];
    }
}
