import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

/**
 * A customer interaction component.
 */
class CustomerInteraction extends FieldComponent {
  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'CustomerInteraction',
        type: 'customerInteraction',
        input: true,
        shouldUpdateCustomerData: true,
        digitalAddressTypes: {
          email: true,
          phoneNumber: true,
        },
        defaultValue: {},
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'CustomerInteraction',
      icon: 'comments',
      group: 'custom_special',
      weight: 300,
      schema: CustomerInteraction.schema(),
    };
  }

  render(content) {
    return super.render(this.renderTemplate('customerInteraction', {}));
  }
}

export default CustomerInteraction;
