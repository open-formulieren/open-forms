import {Formio} from 'formiojs';

const TextField = Formio.Components.components.textfield;

class IbanField extends TextField {
  static schema(...extend) {
    return TextField.schema(
      {
        type: 'iban',
        label: 'IBAN',
        key: 'iban',
        validateOn: 'blur',
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'IBAN Field',
      icon: 'wallet',
      group: 'basic',
      weight: 10,
      schema: IbanField.schema(),
    };
  }

  get defaultSchema() {
    return IbanField.schema();
  }
}

export default IbanField;
