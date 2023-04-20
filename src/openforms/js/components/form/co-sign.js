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
import {getFullyQualifiedUrl} from "../../utils/urls";

const FormioEmail = Formio.Components.components.email;

class CosignField extends FormioEmail {
  static schema(...extend) {
    const schema = FormioEmail.schema(
      {
        type: 'cosign',
        label: 'Co-sign',
        validateOn: 'blur',
        authPlugin: 'digid',
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
        // TODO: Maybe make multiple, so that multiple plugins can be selected?
        {
          type: 'select',
          key: 'authPlugin',
          label: 'Authentication method',
          description:
            'Which authentication method the co-signer must use. Note that this must be an authentication method available on the form.',
          dataSrc: 'url',
          data: {
            // if the url starts with '/', then formio will prefix it with the formio
            // base URL, which is of course wrong. We there explicitly use the detected
            // host.
            url: getFullyQualifiedUrl('/api/v2/authentication/plugins'),
          },
          valueProperty: 'id',
          template: `<span>{{ item.label }}, provides: {{ item.providesAuth }}</span>`,
        },
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

export default CosignField;
