import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const SelectBoxes = Formio.Components.components.selectboxes;

class SelectBoxesField extends SelectBoxes {
  static schema(...extend) {
    const schema = SelectBoxes.schema(
      {
        openForms: {dataSrc: 'manual'},
        values: [{value: '', label: ''}],
        defaultValue: {},
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      ...SelectBoxes.builderInfo,
      schema: SelectBoxesField.schema(),
    };
  }

  constructor(...args) {
    super(...args);

    // somewhere the default emptyValue/defaultValue does not seem to be used and it forces
    // component.defaultValue to be null, which crashes the builder.
    if (this.component.defaultValue === null) {
      this.component.defaultValue = {};
    }
  }

  setSelectedClasses() {
    // In the case the source is a variable, the input.value can be null in the form editor for the default value component
    if (this.dataValue === null) return;

    return super.setSelectedClasses();
  }
}

export default SelectBoxesField;
