import {Formio} from 'formiojs';
import cloneDeep from 'lodash/cloneDeep';

const WebformBuilderFormio = Formio.Builders.builders.webform;

class WebformBuilder extends WebformBuilderFormio {
    constructor() {
        let element, options;
        if (arguments[0] instanceof HTMLElement || arguments[1]) {
            element = arguments[0];
            options = arguments[1];
        }
        else {
            options = arguments[0];
        }

        if (element) {
            super(element, options);
        }
        else {
            super(options);
        }

        const defaultRequiredValue = options.evalContext.requiredDefault;

        // Update the component schema (used by the builder) to change the default value of the 'required' checkbox.
        // This cannot be done directly in the src/openforms/js/components/form/edit/tabs.js file, because the defaultValue
        // property is overwritten by the default given in the Formio Component class (src/components/_classes/component/Component.js:164),
        // which is inherited by all components and used in the builderInfo function.
        let changedComponentSchema = cloneDeep(this.schemas)
        for (const componentSchema in this.schemas) {
            changedComponentSchema[componentSchema].validate = {...componentSchema.validate, required: defaultRequiredValue}
        }
        this.schemas = changedComponentSchema;
    }
}

export default WebformBuilder;
