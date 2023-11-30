import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

/**
 * An address component.
 */
class Address extends FieldComponent {
  constructor(component, options, data) {
    super(component, options, data);
    this.checks = [];
  }

  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'Address',
        type: 'address',
        input: false,
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Address',
      icon: 'home',
      group: 'basic',
      weight: 300,
      schema: Address.schema(),
    };
  }

  render(content) {
    const btnContent = this.t('Address', {
      authPlugin: this.component.authPlugin,
    });
    const context = {
      content: content,
      btnContent: btnContent,
    };
    return super.render(this.renderTemplate('address', context));
  }
}

export default Address;
