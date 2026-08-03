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
export const patchDefaultValue = instance => {
  // #6297; The Formiojs `Component` base class creates a "modified schema" dict
  // (https://github.com/formio/formio.js/blob/v4.13.13/src/components/_classes/component/Component.js#L685C3-L715)
  // which is merged with the default schema to get the component schema. In this
  // `getModifiedSchema` function, empty list values are dropped and get replaced with
  // their default schema values. This results in `defaultValue=[]` being replaced with
  // `defaultValue=""`.
  //
  // With this small fix we ensure that the `defaultValue` correctly represents the
  // `multiple` property.
  if (instance.component.multiple && !Array.isArray(instance.component.defaultValue)) {
    instance.component.defaultValue = [];
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
    patchDefaultValue(this);
  }

  get defaultSchema() {
    return TextField.schema();
  }
}

export default TextField;
