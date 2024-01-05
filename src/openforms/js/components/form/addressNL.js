import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

/**
 * An address (NL) component.
 */
class AddressNL extends FieldComponent {
  constructor(component, options, data) {
    super(component, options, data);
    this.checks = [];
  }

  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'AddressNL',
        type: 'addressNL',
        input: true,
        defaultValue: {},
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'AddressNL',
      icon: 'home',
      group: 'custom_special',
      weight: 300,
      schema: AddressNL.schema(),
    };
  }

  render(content) {
    return super.render(this.renderTemplate('addressNL', {}));
  }
}

export default AddressNL;
