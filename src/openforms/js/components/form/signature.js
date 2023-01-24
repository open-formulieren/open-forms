import {Formio} from 'react-formio';

import {DEFAULT_VALUE, MULTIPLE} from './edit/options';
import {DEFAULT_SENSITIVE_TABS, SENSITIVE_BASIC} from './edit/tabs';
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

  static editForm() {
    const exclude = [DEFAULT_VALUE.key, MULTIPLE.key];
    const choicesSensitiveBasic = {
      key: 'basic',
      label: 'Basic',
      components: [
        ...SENSITIVE_BASIC.components.filter(component => !exclude.includes(component.key)),
      ],
    };
    let defaultSensitiveTabs = {...DEFAULT_SENSITIVE_TABS};
    defaultSensitiveTabs.components[0] = choicesSensitiveBasic;

    return {components: [defaultSensitiveTabs]};
  }
}

export default SignatureField;
