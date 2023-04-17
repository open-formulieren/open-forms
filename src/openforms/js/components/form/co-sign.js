import {Formio} from 'formiojs';

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
} from './edit/options';
import DEFAULT_TABS, {ADVANCED, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';

const FormioEmail = Formio.Components.components.email;

class CosignField extends FormioEmail {
  static schema(...extend) {
    const schema = FormioEmail.schema(
      {
        type: 'cosign',
        validateOn: 'blur',
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
      schema: CosignField.schema(),
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
        PRESENTATION,
        HIDDEN,
        CLEAR_ON_HIDE,
        IS_SENSITIVE_DATA,
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

export default CosignField;
