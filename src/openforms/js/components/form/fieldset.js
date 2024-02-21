import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const FormioFieldSet = Formio.Components.components.fieldset;

class FieldSet extends FormioFieldSet {
  static schema(...extend) {
    return localiseSchema(FormioFieldSet.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...FormioFieldSet.builderInfo,
      schema: FieldSet.schema(),
    };
  }
}

export default FieldSet;
