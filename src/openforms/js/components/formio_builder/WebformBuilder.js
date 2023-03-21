import {Formio} from 'formiojs';
import FormioUtils from 'formiojs/utils';
import BuilderUtils from 'formiojs/utils/builder';
import cloneDeep from 'lodash/cloneDeep';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';
import set from 'lodash/set';

import {getComponentEmptyValue} from 'components/utils';

import {
  addTranslationForLiteral,
  handleComponentValueLiterals,
  isTranslatableProperty,
} from './translation';

const WebformBuilderFormio = Formio.Builders.builders.webform;

class WebformBuilder extends WebformBuilderFormio {
  constructor() {
    super(...arguments);

    const defaultRequiredValue = this.options.evalContext.requiredDefault;

    // Update the component schema (used by the builder) to change the default value of the 'required' checkbox.
    // This cannot be done directly in the src/openforms/js/components/form/edit/tabs.js file, because the defaultValue
    // property is overwritten by the default given in the Formio Component class (src/components/_classes/component/Component.js:164),
    // which is inherited by all components and used in the builderInfo function.
    let changedComponentSchema = cloneDeep(this.schemas);
    for (const componentSchema in this.schemas) {
      let value = defaultRequiredValue;
      const component = changedComponentSchema[componentSchema];
      if (_mayNeverBeRequired(component)) {
        value = false;
      }
      component.validate = {
        ...componentSchema.validate,
        required: value,
      };
    }
    this.schemas = changedComponentSchema;
  }

  // Formio description of this function:
  // *When a component sets its api key, we need to check if it is unique within its namespace. Find the namespace root
  // so we can calculate this correctly.*
  // Since we also need to check the definitions of other form steps, we pass from react the configurations of all the
  // steps as an option to the webform.
  findNamespaceRoot(component) {
    const customNamespace = this.webform?.options?.openForms?.componentNamespace;
    if (!isEmpty(customNamespace)) {
      // exclude components that don't have an ID yet, otherwise the first component of
      // a type gets a key suffixed with '1';
      return customNamespace.filter(comp => !!comp.id);
    }

    return super.findNamespaceRoot(component);
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

    if (!this.editForm) return;

    // find the translations containers so that we can populate translations (initially)
    // and track changes to literals to update the translations. Ideally we'd do this in
    // the onDrop method, but this one has no extension points and A LOT of code to
    // copy :(
    const translationsPathPrefix = 'openForms.translations.';
    const translationComponents = {};
    const {componentTranslationsRef} = this.options.openForms;

    // content components have a different layout
    if (component.type !== 'content') {
      this.editForm.everyComponent(_component => {
        if (_component.type !== 'datagrid') return;
        if (!_component.path.startsWith(translationsPathPrefix)) return;

        const languageCode = _component.path.replace(translationsPathPrefix, '');
        if (languageCode.includes('.') || languageCode.includes('[')) return; // ensure it's a direct child
        translationComponents[languageCode] = _component;
      });
    }

    // this.editForm is a new instance every time the modal opens, so we can track
    // some private state on there.
    if (!this.editForm._ofPreviousLiterals) {
      this.editForm._ofPreviousLiterals = {};
    }

    const updateTranslations = translations => {
      if (component.type === 'content') {
        Object.entries(translations).forEach(([languageCode, translationsForLanguage]) => {
          if (!translationsForLanguage.length) return;
          const {literal, translation} = translationsForLanguage[0];

          // Can't get this to work with FormioUtils.getComponent... it's just skipping
          // over the columns/hidden fields for some reason :(
          let literalComponent;
          let translationComponent;
          this.editForm.everyComponent(_component => {
            const prefix = `openForms.translations.${languageCode}[0].`;
            if (!_component.key.startsWith(prefix)) return;
            const field = _component.key.replace(prefix, '');
            switch (field) {
              case 'literal': {
                literalComponent = _component;
                break;
              }
              case 'translation': {
                translationComponent = _component;
                break;
              }
              default: {
                throw new Error(`Unexpected field ${field}`);
              }
            }
          });
          literalComponent.setValue(literal, {fromSubmission: true});
          translationComponent.setValue(translation, {fromSubmission: true});
        });
      } else {
        Object.entries(translations).forEach(([languageCode, translationsForLanguage]) => {
          const component = translationComponents[languageCode];
          component.setValue(translationsForLanguage, {fromSubmission: true});
        });
      }
    };

    // record all existing translations
    this.editForm.ready.then(() => {
      let translations = {};
      this.editForm.everyComponent(_component => {
        if (_component.path.startsWith(translationsPathPrefix)) return;

        const additionalTranslations = getUpdatedTranslations(
          componentTranslationsRef,
          this.editForm._ofPreviousLiterals,
          _component.path,
          _component.getValue(),
          component
        );
        if (!additionalTranslations) return;
        Object.entries(additionalTranslations).forEach(([langCode, extraTranslations]) => {
          if (!translations[langCode]) translations[langCode] = [];
          translations[langCode].push(...extraTranslations);
        });
      });
      updateTranslations(translations);
    });

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
          let _keyComponent;

          if (!event.data.keyModified && !event.changed.component.isOptionLabel) {
            this.editForm.everyComponent(component => {
              if (component.key === 'key' && component.parent.component.key === 'tabs') {
                _keyComponent = component;
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
            const keyChanged = BuilderUtils.uniquify(formComponents, event.data);
            // #2819 and #2889 - this actually addresses a bug in Formio (reproduced on their hosted builder
            // at https://formio.github.io/formio.js/app/builder).
            // The event.data mutation does fix the data under the hood, but it doesn't cause a re-render of the
            // component where the textfield is entered, still showing the non-unique component key. Using the
            // fromSubmission: true flag triggers a proper redraw.
            if (keyChanged) {
              _keyComponent.setValue(event.data.key, {fromSubmission: true});
            }
          }
        }
      }

      // Handle component translations
      const changedPropertyPath = event.changed.instance.path;
      // can't rely on event.changed.value because that lags behind due to Formio's
      // tiggerChange debounce (?)
      const newValue = get(event.data, changedPropertyPath);

      const newTranslations = getUpdatedTranslations(
        componentTranslationsRef,
        this.editForm._ofPreviousLiterals,
        changedPropertyPath,
        newValue,
        event.data
      );
      if (newTranslations) {
        event.data.openForms.translations = newTranslations;
      }

      // wtaf? if changing the defaultValue, this triggers an infinite change loop
      // for the tabs via updateComponent which modifiers the default value component...
      if (changedPropertyPath === 'tabs') return;

      // Update the component.
      this.updateComponent(event.data.componentJson || event.data, event.changed);

      if (newTranslations && !changedPropertyPath.startsWith(translationsPathPrefix)) {
        updateTranslations(newTranslations);
      }
    };

    // Extract the callback that will be called when a component is changed in the editor
    const existingOnChangeHandlers = this.editForm.events._events['formio.change'];
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
    const fixedComponent = {...component, schema: fixDefaultValues(component)};
    return super.copyComponent(fixedComponent);
  }
}

function fixDefaultValues(component) {
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

/**
 * Check if a given component schema should never be 'required' in the validation aspect.
 *
 * Global configuration can mark components as required by default, but this does not
 * apply to all component types.
 *
 * @param  {Object} component The Component schema to check the type for.
 * @return {Boolean}          True if the component may never be required.
 */
const _mayNeverBeRequired = component => {
  // Issue #1724 - Content components shouldn't be marked as required, since they take no input.
  if (component.type === 'content') {
    return true;
  }

  // Special case for #2548 - an editgrid ('repeating group') itself _can_ be marked
  // required.
  if (component.type === 'editgrid') {
    return false;
  }

  // Issue #2548 - (most) Layout components should never be marked as required since
  // they just group nested components.
  return FormioUtils.isLayoutComponent(component);
};

/**
 * Figure out the new/updated translatable literals in the component.
 */
const getUpdatedTranslations = (
  componentTranslationsRef,
  previousLiterals,
  changedPropertyPath,
  newLiteral,
  newComponentConfiguration
) => {
  // check which translatable properties are relevant
  const {type: componentType} = newComponentConfiguration;
  const localComponentTranslations = componentTranslationsRef.current;

  // the first builder load/iteration sets the values directly by data.values or values,
  // depending on the component type. Subsequent edits of the literals are caught in the
  // normal operation, they show up as data.values[<index>].label and for those the
  // previous literal is properly tracked.
  let newTranslations = handleComponentValueLiterals(
    newComponentConfiguration,
    localComponentTranslations,
    changedPropertyPath,
    newLiteral,
    previousLiterals
  );

  if (newTranslations !== null) return newTranslations;

  if (!isTranslatableProperty(componentType, changedPropertyPath)) return;

  // figure out the previous value of the translation literal for this specific
  // component.
  const prevLiteral = previousLiterals?.[changedPropertyPath];

  // prevent infinite event loops
  if (newLiteral == prevLiteral) return;

  // update the translations
  newTranslations = addTranslationForLiteral(
    newComponentConfiguration,
    localComponentTranslations,
    prevLiteral,
    newLiteral
  );
  set(previousLiterals, [changedPropertyPath], newLiteral);
  return newTranslations;
};

export default WebformBuilder;
