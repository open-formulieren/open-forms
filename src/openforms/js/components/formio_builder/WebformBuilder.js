import {Formio} from 'formiojs';
import BuilderUtils from 'formiojs/utils/builder';
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

    editComponent(component, parent, isNew, isJsonEdit, original, flags = {}) {

        const componentCopy = cloneDeep(component);
        const parentEditResult = super.editComponent(component, parent, isNew, isJsonEdit, original, flags);

        // Extract the callback that will be called when a component is changed in the editor
        const existingOnChangeHandlers = this.editForm.events._events['formio.change'];

        const modifiedOnChangeCallback = (event) => {
            // Issue #1422 - This callback is a modified version of:
            // https://github.com/formio/formio.js/blob/4.13.x/src/WebformBuilder.js#L1347
            // The issue is that when a component in the editForm with key 'label' is updated, the key of the main
            // component is reset. For Radio buttons / selectboxes, there are multiple fields in the editForm with key
            // 'label': the label of the component and the labels of the options. From within the
            // this.editForm.everyComponent function it didn't seem possible to differentiate which component was being
            // edited. So, to prevent changes to the options labels to reset the key, a custom option "isOptionLabel"
            // was added to them in src/openforms/js/components/form/edit/tabs.js.
            if (!event.changed) return;

            if (event.changed.component && event.changed.component.key === 'showFullSchema') {
                const { value } = event.changed;
                this.editForm.submission = {
                    data: {
                        componentJson: component,
                        showFullSchema: value
                    },
                };
                return;
            }

            // See if this is a manually modified key. Treat custom component keys as manually modified
            if ((event.changed.component && (event.changed.component.key === 'key')) || isJsonEdit) {
                componentCopy.keyModified = true;
            }

            if (event.changed.component && (['label', 'title'].includes(event.changed.component.key))) {
                // Ensure this component has a key.
                if (isNew) {
                    if (!event.data.keyModified && !event.changed.component.isOptionLabel) {
                        this.editForm.everyComponent(component => {
                            if (component.key === 'key' && component.parent.component.key === 'tabs') {
                                component.setValue(_.camelCase(
                                    event.data.title ||
                                    event.data.label ||
                                    event.data.placeholder ||
                                    event.data.type
                                ).replace(/^[0-9]*/, '') );

                                return false;
                            }
                        });
                    }

                    if (this.form) {
                        let formComponents = this.findNamespaceRoot(parent.formioComponent);
                        // excluding component which key uniqueness is to be checked to prevent the comparing of the same keys
                        formComponents = formComponents.filter(
                            comp => this.editForm.options.editComponent.id !== comp.id
                        );

                        // Set a unique key for this component.
                        BuilderUtils.uniquify(formComponents, event.data);
                    }
                }
            }

            // Update the component.
            this.updateComponent(event.data.componentJson || event.data, event.changed);
        };

        this.editForm.events._events['formio.change'][existingOnChangeHandlers.length-1].fn = modifiedOnChangeCallback;
        return parentEditResult;
    }
}

export default WebformBuilder;
