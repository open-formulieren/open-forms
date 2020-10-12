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
     * Returns the URL for this Form.
     * @return {string}
     */
    getAbsoluteUrl() {
        return `/${this.uuid}`;
    }

    /**
     * Reads the current FormStep for this Form.
     * @param {(number|null)} [stepUUID=null] The uuid of the step to load, loads current step if omitted.
     * @return {Promise}
     */
    readCurrentStep(stepUUID=null) {
        if (stepUUID === null) {
            return this.formStepConsumer.read(this, this.user_current_step);
        }

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
