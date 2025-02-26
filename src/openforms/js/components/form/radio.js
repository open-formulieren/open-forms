import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const RadioFormio = Formio.Components.components.radio;

class RadioField extends RadioFormio {
  static schema(...extend) {
    const schema = RadioFormio.schema(
      {
        // Issue #2538 - If the dataType is not specified, Formio will try to parse the values. This means that if the
        // keys of the values are 1, true they will be added to the submission data as float/bool instead of string.
        dataType: 'string',
        // types expect values set and not null/undefined
        openForms: {dataSrc: 'manual'},
        values: [{value: '', label: ''}],
        defaultValue: '',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Radio',
      group: 'basic',
      icon: 'dot-circle-o',
      weight: 80,
      documentation: '/userguide/forms/form-components#radio',
      schema: RadioField.schema(),
    };
  }

  setSelectedClasses() {
    // In the case the source is a variable, the input.value can be null in the form editor for the default value component
    if (this.dataValue === null) return;

    return super.setSelectedClasses();
  }

  get defaultSchema() {
    return RadioField.schema();
  }
}

export default RadioField;
