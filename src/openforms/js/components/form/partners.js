import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

/**
 * A partners component.
 */
class Partners extends FieldComponent {
  constructor(component, options, data) {
    super(component, options, data);
    this.checks = [];
  }

  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'Partners',
        type: 'partners',
        input: true,
        defaultValue: [],
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Partners',
      icon: 'users',
      group: 'custom_special',
      weight: 300,
      schema: Partners.schema(),
    };
  }

  render(content) {
    return super.render(this.renderTemplate('partners', {}));
  }
}

export default Partners;
