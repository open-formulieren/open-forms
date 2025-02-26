import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FormioTextField = Formio.Components.components.textfield;

export const patchValidateDefaults = instance => {
  // Formio.js itself doesn't respect their own typescript declarations...
  // https://github.com/formio/formio.js/blob/master/src/components/textfield/TextField.js#L21
  // So we patch up these badly typed default values, letting the default behaviour of
  // our own formio-builder kick in.
  // Fixing this in static schema doesn't seem to apply it to component instances (?),
  // so we need to patch the weird typing information here.
  const validate = instance.component?.validate;

  if (validate?.minLength === '') {
    delete validate.minLength;
  }
  if (validate?.maxLength === '') {
    delete validate.maxLength;
  }

  if (validate?.minWords === '') {
    delete validate.minWords;
  }
  if (validate?.maxWords === '') {
    delete validate.maxWords;
  }
};

class TextField extends FormioTextField {
  static schema(...extend) {
    return localiseSchema(FormioTextField.schema({defaultValue: ''}, ...extend));
  }

  static get builderInfo() {
    return {
      ...FormioTextField.builderInfo,
      schema: TextField.schema(),
    };
  }

  constructor(...args) {
    super(...args);

    patchValidateDefaults(this);
  }

  get defaultSchema() {
    return TextField.schema();
  }
}

export default TextField;
