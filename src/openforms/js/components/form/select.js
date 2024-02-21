import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const Select = Formio.Components.components.select;

class SelectField extends Select {
  static schema(...extend) {
    const schema = Select.schema(
      {
        openForms: {dataSrc: 'manual'},
        values: [{value: '', label: ''}],
        defaultValue: '',
      },
      ...extend
    );
    return localiseSchema({...schema, key: 'select-key'});
  }

  static get builderInfo() {
    return {
      ...Select.builderInfo,
      schema: SelectField.schema(),
    };
  }
}

export default SelectField;
