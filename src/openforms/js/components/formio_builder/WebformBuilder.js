import {ComponentConfiguration} from '@open-formulieren/formio-builder';
import BUILDER_REGISTRY from '@open-formulieren/formio-builder/esm/registry';
import {Formio} from 'formiojs';
import Components from 'formiojs/components/Components';
import FormioUtils from 'formiojs/utils';
import BuilderUtils from 'formiojs/utils/builder';
import {produce} from 'immer';
import cloneDeep from 'lodash/cloneDeep';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';
import set from 'lodash/set';
import React from 'react';
import {createRoot} from 'react-dom/client';
import {IntlProvider} from 'react-intl';

import {getIntlProviderProps} from 'components/admin/i18n';
import {getAvailableAuthPlugins} from 'components/form/cosign';
import {getAvailableDocumentTypes} from 'components/form/file';
import {getComponentEmptyValue} from 'components/utils';
import jsonScriptToVar from 'utils/json-script';

import {
  getPrefillAttributes,
  getPrefillPlugins,
  getRegistrationAttributes,
  getValidatorPlugins,
} from './plugins';
import {
  LANGUAGES,
  addTranslationForLiteral,
  handleComponentValueLiterals,
  isTranslatableProperty,
} from './translation';

const CONFIDENTIALITY_LEVELS = jsonScriptToVar('CONFIDENTIALITY_LEVELS', {default: []});
const FILE_TYPES = jsonScriptToVar('config-UPLOAD_FILETYPES', {default: []});
const MAX_FILE_UPLOAD_SIZE = jsonScriptToVar('setting-MAX_FILE_UPLOAD_SIZE', {default: 'unknown'});
const RICH_TEXT_COLORS = jsonScriptToVar('config-RICH_TEXT_COLORS', {default: []});

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

  /*
    The legacy editComponent implementation, with our own overrides. This uses the
    Formio builder/renderer rendering inside the modal.

    Remove this method once all component types are supported in
    @open-formulieren/formio-builder for React-based rendering.
   */
  LEGACY_editComponent(component, parent, isNew, isJsonEdit, original, flags = {}) {
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

  // Custom react-based implementation
  editComponent(component, parent, isNew, isJsonEdit, original, flags = {}) {
    const {react_formio_builder_enabled = false} = this.options.openForms.featureFlags;

    if (
      !component.key ||
      !react_formio_builder_enabled ||
      !BUILDER_REGISTRY.hasOwnProperty(component.type)
    ) {
      return this.LEGACY_editComponent(component, parent, isNew, isJsonEdit, original, flags);
    }

    if (!component.key) {
      return;
    }

    if (!component.id) {
      component.id = FormioUtils.getRandomComponentId();
    }

    let saved = false;
    // using only produce seems to affect component itself, which crashes the preview
    // rebuild of formio...
    // const componentCopy = produce(component, draft => draft);
    const componentCopy = produce(FormioUtils.fastCloneDeep(component), draft => draft);
    const ComponentClass = Components.components[componentCopy.type];

    // Make sure we only have one dialog open at a time.
    if (this.dialog) {
      this.dialog.close();
      this.highlightInvalidComponents();
    }

    this.componentEdit = this.ce('div', {class: 'component-edit-container'});
    const root = createRoot(this.componentEdit);

    const onCancel = event => {
      event.preventDefault();
      root.unmount();
      this.emit('cancelComponent', component);
      this.dialog.close();
      this.highlightInvalidComponents();
    };

    const onRemove = event => {
      event.preventDefault();
      // Since we are already removing the component, don't trigger another remove.
      saved = true;
      root.unmount();
      this.removeComponent(component, parent, original);
      this.dialog.close();
      this.highlightInvalidComponents();
    };

    const onSubmit = componentData => {
      saved = true;
      root.unmount();
      // we can't use the original saveComponent, as it relies on this.editForm being
      // a thing, which it isn't anymore here.
      this.dialog.close();
      this.saveComponentReact(componentData, parent, isNew, original);
      this.highlightInvalidComponents();
    };

    const uniquifyKey = key => {
      const temp = {key};
      const formComponents = this.findNamespaceRoot(parent.formioComponent).filter(
        comp => comp.id !== component.id
      );
      // this mutates instead of returning a unique key...
      BuilderUtils.uniquify(formComponents, temp);
      return temp.key;
    };

    // hand contents of modal over to React
    (async () => {
      const intlProviderProps = await getIntlProviderProps();
      root.render(
        <IntlProvider {...intlProviderProps}>
          <ComponentConfiguration
            // Context binding
            uniquifyKey={uniquifyKey}
            supportedLanguageCodes={LANGUAGES}
            richTextColors={RICH_TEXT_COLORS}
            getFormComponents={() => parent.formioContainer}
            getValidatorPlugins={getValidatorPlugins}
            getRegistrationAttributes={getRegistrationAttributes}
            getPrefillPlugins={getPrefillPlugins}
            getPrefillAttributes={getPrefillAttributes}
            getFileTypes={async () => FILE_TYPES}
            serverUploadLimit={MAX_FILE_UPLOAD_SIZE}
            getDocumentTypes={async () => await getAvailableDocumentTypes(this)}
            getConfidentialityLevels={async () => CONFIDENTIALITY_LEVELS}
            getAuthPlugins={getAvailableAuthPlugins}
            // Component/builder state
            isNew={isNew}
            component={componentCopy}
            builderInfo={ComponentClass.builderInfo}
            onCancel={onCancel}
            onRemove={onRemove}
            onSubmit={onSubmit}
          />
        </IntlProvider>
      );
      // Create and open the modal - contents are managed by React component.
      this.dialog = this.createModal(this.componentEdit, get(this.options, 'dialogAttr', {}));

      const dialogClose = () => {
        if (isNew && !saved) {
          this.removeComponent(component, parent, original);
          this.highlightInvalidComponents();
        }
        // Clean up.
        this.removeEventListener(this.dialog, 'close', dialogClose);
        this.dialog = null;
      };
      this.addEventListener(this.dialog, 'close', dialogClose);

      // Called when we edit a component.
      this.emit('editComponent', component);
    })();
  }

  /**
   * saveComponent method when triggered from React events/formio builder.
   *
   * This mostly replicates the logic of saveComponent, but doesn't support
   * submissionData/json editing.
   */
  saveComponentReact(componentData, parent, isNew, original) {
    const parentContainer = parent ? parent.formioContainer : this.container;
    const parentComponent = parent ? parent.formioComponent : this;
    const path = parentContainer
      ? this.getComponentsPath(componentData, parentComponent.component)
      : '';
    if (!original) {
      original = parent.formioContainer.find(comp => comp.id === componentData.id);
    }
    const index = parentContainer ? parentContainer.indexOf(original) : 0;
    // not found, abort early
    if (index === -1) {
      this.highlightInvalidComponents();
      return NativePromise.resolve();
    }

    // not-so-elegant input sanitation that formio does... FIXME: can't we just escape
    // this with \" instead?
    if (componentData) {
      ['label', 'tooltip', 'placeholder'].forEach(property => {
        if (!componentData[property]) return;
        componentData[property] = componentData[property].replace(/"/g, "'");
      });
    }

    // look up the component instance with the parent
    let componentInstance = null;
    parentComponent.getComponents().forEach(childComponent => {
      // Changed from Formio. We do the check on id and not on key
      // (as this causes problems in the case of duplicate keys)
      if (childComponent.component.id === original.id) {
        componentInstance = childComponent;
      }
    });
    const originalComp = componentInstance.component;
    const originalComponentSchema = componentInstance.schema;
    const isParentSaveChildMethod = this.isParentSaveChildMethod(parent.formioComponent);

    if (parentContainer && !isParentSaveChildMethod) {
      parentContainer[index] = componentData;
      if (componentInstance) {
        componentInstance.component = componentData;
      }
    } else if (isParentSaveChildMethod) {
      parent.formioComponent.saveChildComponent(componentData);
    }

    const rebuild = parentComponent.rebuild() || Promise.resolve();
    return rebuild.then(() => {
      const schema = parentContainer
        ? parentContainer[index]
        : componentInstance
        ? componentInstance.schema
        : [];
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
