import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

/**
 * A customer profile component.
 */
class CustomerProfile extends FieldComponent {
  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'Profile',
        type: 'customerProfile',
        input: true,
        shouldUpdateCustomerData: true,
        digitalAddressTypes: ['email', 'phoneNumber'],
        defaultValue: undefined,
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Profile',
      icon: 'comments',
      group: 'custom_special',
      weight: 300,
      schema: CustomerProfile.schema(),
    };
  }

  render(content) {
    return super.render(this.renderTemplate('customerProfile', {}));
  }
}

export default CustomerProfile;
