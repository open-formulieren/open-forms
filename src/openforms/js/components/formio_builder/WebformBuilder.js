import {Formio} from 'formiojs';
import FormioUtils from 'formiojs/utils';
import BuilderUtils from 'formiojs/utils/builder';
import cloneDeep from 'lodash/cloneDeep';

import {getComponentEmptyValue} from 'components/utils';

const WebformBuilderFormio = Formio.Builders.builders.webform;

class WebformBuilder extends WebformBuilderFormio {
  constructor() {
    let element, options;
    if (arguments[0] instanceof HTMLElement || arguments[1]) {
      element = arguments[0];
      options = arguments[1];
    } else {
      options = arguments[0];
    }

    if (element) {
      super(element, options);
    } else {
      super(options);
    }

    const defaultRequiredValue = options.evalContext.requiredDefault;

    // Update the component schema (used by the builder) to change the default value of the 'required' checkbox.
    // This cannot be done directly in the src/openforms/js/components/form/edit/tabs.js file, because the defaultValue
    // property is overwritten by the default given in the Formio Component class (src/components/_classes/component/Component.js:164),
    // which is inherited by all components and used in the builderInfo function.
    let changedComponentSchema = cloneDeep(this.schemas);
    for (const componentSchema in this.schemas) {
      let value = defaultRequiredValue;
      // Issue #1724 - Content components shouldn't be marked as required, since they take no input.
      if (changedComponentSchema[componentSchema].type === 'content') {
        value = false;
      }

      changedComponentSchema[componentSchema].validate = {
        ...componentSchema.validate,
        required: value,
      };
    }
    this.schemas = changedComponentSchema;
  }

  editComponent(component, parent, isNew, isJsonEdit, original, flags = {}) {
    const componentCopy = cloneDeep(component);
    const parentEditResult = super.editComponent(
      component,
      parent,
      isNew,
      isJsonEdit,
      original,
      flags
    );

    // Extract the callback that will be called when a component is changed in the editor
    if (!this.editForm) return;
    const existingOnChangeHandlers = this.editForm.events._events['formio.change'];

    const modifiedOnChangeCallback = event => {
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
        const {value} = event.changed;
        this.editForm.submission = {
          data: {
            componentJson: component,
            showFullSchema: value,
          },
        };
        return;
      }

      // See if this is a manually modified key. Treat custom component keys as manually modified
      if ((event.changed.component && event.changed.component.key === 'key') || isJsonEdit) {
        componentCopy.keyModified = true;
      }

      if (event.changed.component && ['label', 'title'].includes(event.changed.component.key)) {
        // Ensure this component has a key.
        if (isNew) {
          if (!event.data.keyModified && !event.changed.component.isOptionLabel) {
            this.editForm.everyComponent(component => {
              if (component.key === 'key' && component.parent.component.key === 'tabs') {
                component.setValue(
                  _.camelCase(
                    event.data.title ||
                      event.data.label ||
                      event.data.placeholder ||
                      event.data.type
                  ).replace(/^[0-9]*/, '')
                );

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

    if (existingOnChangeHandlers.length) {
      this.editForm.events._events['formio.change'][existingOnChangeHandlers.length - 1].fn =
        modifiedOnChangeCallback;
    }
    return parentEditResult;
  }

  saveComponent(component, parent, isNew, original) {
    this.editForm.detach();
    const parentContainer = parent ? parent.formioContainer : this.container;
    const parentComponent = parent ? parent.formioComponent : this;
    this.dialog.close();
    const path = parentContainer
      ? this.getComponentsPath(component, parentComponent.component)
      : '';
    if (!original) {
      original = parent.formioContainer.find(comp => comp.id === component.id);
    }
    const index = parentContainer ? parentContainer.indexOf(original) : 0;
    if (index !== -1) {
      let submissionData = this.editForm.submission.data;
      submissionData = submissionData.componentJson || submissionData;
      const fieldsToRemoveDoubleQuotes = ['label', 'tooltip', 'placeholder'];

      if (submissionData) {
        fieldsToRemoveDoubleQuotes.forEach(key => {
          if (submissionData[key]) {
            submissionData[key] = submissionData[key].replace(/"/g, "'");
          }
        });
      }

      let comp = null;
      parentComponent.getComponents().forEach(component => {
        // Changed from Formio. We do the check on id and not on key
        // (as this causes problems in the case of duplicate keys)
        if (component.component.id === original.id) {
          comp = component;
        }
      });
      const originalComp = comp.component;
      const originalComponentSchema = comp.schema;

      const isParentSaveChildMethod = this.isParentSaveChildMethod(parent.formioComponent);

      if (parentContainer && !isParentSaveChildMethod) {
        parentContainer[index] = submissionData;
        if (comp) {
          comp.component = submissionData;
        }
      } else if (isParentSaveChildMethod) {
        parent.formioComponent.saveChildComponent(submissionData);
      }

      const rebuild = parentComponent.rebuild() || Promise.resolve();
      return rebuild.then(() => {
        const schema = parentContainer ? parentContainer[index] : comp ? comp.schema : [];
        this.emitSaveComponentEvent(
          schema,
          originalComp,
          parentComponent.schema,
          path,
          index,
          isNew,
          originalComponentSchema
        );
        this.emit('change', this.form);
        this.highlightInvalidComponents();
      });
    }

    this.highlightInvalidComponents();
    return Promise.resolve();
  }

  // Taken from https://github.com/formio/formio.js/blob/v4.13.13/src/WebformBuilder.js#L1450
  // Modified so that copied components have the right defaultValue
  copyComponent(component) {
    if (!window.sessionStorage) {
      return console.warn('Session storage is not supported in this browser.');
    }
    this.addClass(this.refs.form, 'builder-paste-mode');
    window.sessionStorage.setItem(
      'formio.clipboard',
      JSON.stringify(this.fixDefaultValues(component))
    );
  }

  fixDefaultValues(component) {
    // #2213 - Copied textField components had null defaultValue instead of the right empty value
    const updatedSchema = {defaultValue: component.emptyValue, ...component.schema};

    // #2436 - Copied fieldsets with components inside give the wrong default value for the nested components
    if (FormioUtils.isLayoutComponent(updatedSchema)) {
      const components = updatedSchema.components || updatedSchema.columns || updatedSchema.rows;
      FormioUtils.eachComponent(components, component => {
        if (component.defaultValue == null) {
          // Cheeky workaround to get the empty value of components. Once inside the eachComponent(), we only have
          // access to the schema and not the component instance
          component.defaultValue = getComponentEmptyValue(component);
        }
      });
    }
    return updatedSchema;
  }
}

export default WebformBuilder;
