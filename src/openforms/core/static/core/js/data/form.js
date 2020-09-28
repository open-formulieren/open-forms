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
        return `/${this.slug}`;
    }

    /**
     * Reads the current FormStep for this Form.
     * @param {(number|null)} [stepIndex=null] The index of the step to load, loads current step if omitted.
     * @return {Promise}
     */
    readCurrentStep(stepIndex=null) {
        if (stepIndex === null) {
            return this.formStepConsumer.read(this, this.user_current_step.index);
        }
        return this.formStepConsumer.read(this, stepIndex);
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
