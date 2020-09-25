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
     * Reads the current FormStep for this Form.
     * @return {Promise}
     */
    readCurrentStep() {
        const stepIndex =  this.user_current_step.index;
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
    }
}
