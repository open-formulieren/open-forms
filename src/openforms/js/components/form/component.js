import {Formio} from 'formiojs';

const FormioComponent = Formio.Components.components.component;

function getDataValue() {
  const empty = this.component.multiple ? [] : this.emptyValue;
  if (!this.key || (!this.visible && this.component.clearOnHide && !this.rootPristine)) {
    this.dataValue = empty;
    return empty;
  }

  if (!this.hasValue()) {
    // #2213 - TextField has a different defaultValue depending on whether the editForm has been modified or not.
    // This function is taken from https://github.com/formio/formio.js/blob/v4.13.13/src/components/_classes/component/Component.js#L2240
    // and modified so that the default value is set also for pristine editForms.
    this.dataValue = empty;
    return empty;
  }
  return _.get(this._data, this.key);
}

class Component extends FormioComponent {
  get dataValue() {
    return getDataValue.call(this);
  }
}

/**
 * Override prototype of all components
 *
 * Formio components have an inheritance chain where each concrete field extends from
 * the Field component, which in turn extends the Component field. So, our custom
 * Component class above is NOT used in those inheritance chains.
 *
 * This means that we have two options: repeating the dataValue override for every
 * TextField component we use and having a lot of code repetition, or modifying the prototype
 * used in the inheritance chain once to replace the default dataValue getter. The
 * latter option is the more maintainable one and that's exactly what happens below.
 */
Object.defineProperty(FormioComponent.prototype, 'dataValue', {
  get: function () {
    return getDataValue.call(this);
  },
});

export default Component;
