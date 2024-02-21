import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const TextField = Formio.Components.components.textfield;

class LicensePlate extends TextField {
  static schema(...extend) {
    const schema = TextField.schema(
      {
        type: 'licenseplate',
        label: 'License plate',
        key: 'licenseplate',
        validateOn: 'blur',
        validate: {
          pattern: '^[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}\\-[a-zA-Z0-9]{1,3}$',
        },
        errors: {
          pattern: 'Invalid Dutch license plate',
        },
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'License plate',
      icon: 'car',
      group: 'basic',
      weight: 10,
      schema: LicensePlate.schema(),
    };
  }

  get defaultSchema() {
    return LicensePlate.schema();
  }
}

export default LicensePlate;
