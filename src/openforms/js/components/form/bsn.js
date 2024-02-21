import TextField from './textfield';

class BsnField extends TextField {
  static schema(...extend) {
    return TextField.schema(
      {
        type: 'bsn',
        label: 'BSN',
        key: 'bsn',
        inputMask: '999999999',
        validateOn: 'blur',
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'BSN Field',
      icon: 'id-card-o',
      group: 'basic',
      weight: 10,
      schema: BsnField.schema(),
    };
  }

  get defaultSchema() {
    return BsnField.schema();
  }
}

export default BsnField;
