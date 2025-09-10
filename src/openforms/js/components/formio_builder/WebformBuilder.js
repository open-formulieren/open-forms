import {ComponentConfiguration} from '@open-formulieren/formio-builder';
import {Formio} from 'formiojs';
import Components from 'formiojs/components/Components';
import FormioUtils from 'formiojs/utils';
import BuilderUtils from 'formiojs/utils/builder';
import {produce} from 'immer';
import cloneDeep from 'lodash/cloneDeep';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';
import {createRoot} from 'react-dom/client';
import {IntlProvider} from 'react-intl';

import {getIntlProviderProps} from 'components/admin/i18n';
import {getAvailableAuthPlugins} from 'components/form/cosign';
import {getAvailableDocumentTypes} from 'components/form/file';
import {getComponentEmptyValue} from 'components/utils';
import jsonScriptToVar from 'utils/json-script';
import {sanitizeHTML} from 'utils/sanitize';
import {currentTheme} from 'utils/theme';

import {
  getPrefillAttributes,
  getPrefillPlugins,
  getRegistrationAttributes,
  getValidatorPlugins,
} from './plugins';
import {getReferenceListsTableItems, getReferenceListsTables, getServices} from './referenceLists';

let _supportedLanguages = undefined;
const getSupportedLanguages = () => {
  if (_supportedLanguages !== undefined) return _supportedLanguages;
  _supportedLanguages = jsonScriptToVar('languages', {default: []});
  return _supportedLanguages;
};

const LANGUAGES = getSupportedLanguages().map(([langCode]) => langCode);
const CONFIDENTIALITY_LEVELS = jsonScriptToVar('CONFIDENTIALITY_LEVELS', {default: []});
const FILE_TYPES = jsonScriptToVar('config-UPLOAD_FILETYPES', {default: []});
const MAX_FILE_UPLOAD_SIZE = jsonScriptToVar('setting-MAX_FILE_UPLOAD_SIZE', {default: 'unknown'});
const RICH_TEXT_COLORS = jsonScriptToVar('config-RICH_TEXT_COLORS', {default: []});
const MAP_TILE_LAYERS = jsonScriptToVar('config-MAP_TILE_LAYERS', {default: []});

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
        ...component.validate,
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

  // Custom react-based implementation
  editComponent(component, parent, isNew, isJsonEdit, original, flags = {}) {
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
    const componentCopy = FormioUtils.fastCloneDeep(component);
    const ComponentClass = Components.components[componentCopy.type];

    // takes care of setting the defaults from the schema etc., since `component` itself
    // is really just the bare minimum and may not comply with our TypeScript definitions.
    const instance = new ComponentClass(componentCopy);
    const builderData = produce(instance.component, draft => draft);

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

    // this context is not available when editing a form definition (standalone)
    const {authBackends = [], availablePrefillPlugins = []} = this.webform?.options?.openForms;

    // hand contents of modal over to React
    (async () => {
      const intlProviderProps = await getIntlProviderProps();

      root.render(
        <IntlProvider {...intlProviderProps}>
          <ComponentConfiguration
            // Context binding
            uniquifyKey={uniquifyKey}
            supportedLanguageCodes={LANGUAGES}
            theme={currentTheme.getValue()}
            richTextColors={RICH_TEXT_COLORS}
            getMapTileLayers={async () => MAP_TILE_LAYERS}
            getFormComponents={() => this.webform.form.components}
            getValidatorPlugins={getValidatorPlugins}
            getRegistrationAttributes={getRegistrationAttributes}
            getServices={getServices}
            getReferenceListsTables={getReferenceListsTables}
            getReferenceListsTableItems={getReferenceListsTableItems}
            getPrefillPlugins={getPrefillPlugins}
            getPrefillAttributes={async plugin =>
              await getPrefillAttributes(plugin, {
                authBackends,
                availablePrefillPlugins,
              })
            }
            getFileTypes={async () => FILE_TYPES}
            serverUploadLimit={MAX_FILE_UPLOAD_SIZE}
            getDocumentTypes={async () => await getAvailableDocumentTypes(this)}
            getConfidentialityLevels={async () => CONFIDENTIALITY_LEVELS}
            getAuthPlugins={getAvailableAuthPlugins}
            // Component/builder state
            isNew={isNew}
            component={builderData}
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
        root.unmount();
      };
      this.addEventListener(this.dialog, 'close', dialogClose);

      // Called when we edit a component.
      this.emit('editComponent', component);
    })();
  }

  sanitizeComponentData(componentData) {
    ['label', 'tooltip', 'description'].forEach(property => {
      if (!componentData[property]) return;
      componentData[property] = sanitizeHTML(componentData[property]);
    });

    // not-so-elegant input sanitation that formio does... FIXME: can't we just escape
    // this with \" instead?
    ['label', 'tooltip', 'placeholder'].forEach(property => {
      if (!componentData[property]) return;
      componentData[property] = componentData[property].replace(/"/g, "'");
    });

    return componentData;
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

    if (componentData) {
      // Perform some basic component data sanitizing
      componentData = this.sanitizeComponentData(componentData);
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

  // Issue #5090 - Soft required components shouldn't be marked as required, since they take no input.
  if (component.type === 'softRequiredErrors') {
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

export default WebformBuilder;
