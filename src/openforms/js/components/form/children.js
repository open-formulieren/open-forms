import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FieldComponent = Formio.Components.components.field;

/**
 * A children component.
 */
class Children extends FieldComponent {
  constructor(component, options, data) {
    super(component, options, data);
    this.checks = [];
  }

  static schema(...extend) {
    const schema = FieldComponent.schema(
      {
        label: 'Children',
        type: 'children',
        input: true,
        enableSelection: false,
        defaultValue: [],
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Children',
      icon: 'children',
      group: 'custom_special',
      weight: 300,
      schema: Children.schema(),
    };
  }

  render(content) {
    return super.render(this.renderTemplate('children', {}));
  }
}

export default Children;
