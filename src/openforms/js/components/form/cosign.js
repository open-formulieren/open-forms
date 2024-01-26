import {Formio} from 'formiojs';

import {AUTH_PLUGINS_ENDPOINT} from 'components/admin/form_design/constants.js';
import {get} from 'utils/fetch';

import {
  AUTOCOMPLETE,
  CLEAR_ON_HIDE,
  DEFAULT_VALUE,
  DESCRIPTION,
  HIDDEN,
  IS_SENSITIVE_DATA,
  KEY,
  LABEL_REQUIRED,
  PRESENTATION,
  TOOLTIP,
} from './edit/options';
import DEFAULT_TABS, {ADVANCED, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';

export const getAvailableAuthPlugins = async () => {
  const response = await get(AUTH_PLUGINS_ENDPOINT);
  return response.data;
};

const FormioEmail = Formio.Components.components.email;

class CoSignField extends FormioEmail {
  constructor(...args) {
    super(...args);

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

  static editForm() {
    const BASIC_TAB = {
      key: 'basic',
      label: 'Basic',
      components: [
        LABEL_REQUIRED,
        KEY,
        DESCRIPTION,
        TOOLTIP,
        PRESENTATION,
        HIDDEN,
        CLEAR_ON_HIDE,
        {...IS_SENSITIVE_DATA, defaultValue: true},
        DEFAULT_VALUE,
        {...AUTOCOMPLETE, placeholder: 'email'},
      ],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default CoSignField;
