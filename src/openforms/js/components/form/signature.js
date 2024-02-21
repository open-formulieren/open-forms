import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const Signature = Formio.Components.components.signature;

class SignatureField extends Signature {
  static schema(...extend) {
    return localiseSchema(Signature.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...Signature.builderInfo,
      schema: localiseSchema(SignatureField.schema()),
    };
  }
}

export default SignatureField;
