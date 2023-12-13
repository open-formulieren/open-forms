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
        input: false,
        defaultValue: {}
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

  // render(content) {
  //   const btnContent = this.t('AddressNL', {
  //     authPlugin: this.component.authPlugin,
  //   });
  //   const context = {
  //     content: content,
  //     btnContent: btnContent,
  //   };
  //   return super.render(this.renderTemplate('addressNL', context));
  // }
}

export default AddressNL;
