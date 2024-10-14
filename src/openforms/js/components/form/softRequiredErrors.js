import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const FormioContentField = Formio.Components.components.content;

const Component = Formio.Components.components.component;

class SoftRequiredErrors extends FormioContentField {
  static schema(...extend) {
    const schema = Component.schema(
      {
        type: 'softRequiredErrors',
        key: 'softRequiredErrors',
        label: '', // not displayed anyway
        input: false,
        html: undefined, // use default defined in formio-builder
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Soft required errors',
      icon: 'triangle-exclamation',
      group: 'custom_layout',
      weight: 900,
      schema: this.schema(),
    };
  }
}

export default SoftRequiredErrors;
