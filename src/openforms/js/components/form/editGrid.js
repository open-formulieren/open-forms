import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const EditGridFormio = Formio.Components.components.editgrid;

class EditGrid extends EditGridFormio {
  static schema(...extend) {
    const schema = EditGridFormio.schema(
      {
        label: 'Repeating Group',
        key: 'repeatingGroup',
        hideLabel: false,
        inlineEdit: false,
      },
      ...extend
    );
    return localiseSchema(schema);
  }
  static get builderInfo() {
    return {
      hideLabel: false,
      title: 'Repeating Group',
      icon: 'repeat',
      schema: EditGrid.schema(),
    };
  }
}

export default EditGrid;
