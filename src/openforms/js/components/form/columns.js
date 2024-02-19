import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const FormioColumnField = Formio.Components.components.columns;

class ColumnField extends FormioColumnField {
  static schema(...extend) {
    const schema = FormioColumnField.schema(
      {
        label: 'Columns',
        key: 'columns',
        type: 'columns',
        columns: [
          {size: 6, components: []},
          {size: 6, components: []},
        ],
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Columns',
      icon: 'columns',
      group: 'layout',
      documentation: '/userguide/#columns',
      weight: 10,
      schema: ColumnField.schema(),
    };
  }

  get defaultSchema() {
    return ColumnField.schema();
  }
}

export default ColumnField;
