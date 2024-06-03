import {Formio} from 'formiojs';

import {AUTH_PLUGINS_ENDPOINT} from 'components/admin/form_design/constants.js';
import {get} from 'utils/fetch';

import {localiseSchema} from './i18n';
import {patchValidateDefaults} from './textfield';

export const getAvailableAuthPlugins = async () => {
  const response = await get(AUTH_PLUGINS_ENDPOINT);
  return response.data;
};

const FormioEmail = Formio.Components.components.email;

class CoSignField extends FormioEmail {
  constructor(...args) {
    super(...args);

    patchValidateDefaults(this);

    // somewhere the default emptyValue/defaultValue does not seem to be used and it forces
    // component.defaultValue to be null, which crashes the builder.
    if (this.component.defaultValue === null) {
      this.component.defaultValue = '';
    }
  }

  static schema(...extend) {
    const schema = FormioEmail.schema(
      {
        type: 'cosign',
        key: 'cosign',
        label: 'Co-signer email address',
        validateOn: 'blur',
        defaultValue: '',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Co-sign',
      group: 'advanced',
      icon: 'pen-nib',
      schema: CoSignField.schema(),
    };
  }
}

export default CoSignField;
