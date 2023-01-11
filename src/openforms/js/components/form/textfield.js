import {Formio} from 'react-formio';

import {
  ADVANCED,
  LOCATION,
  PREFILL,
  REGISTRATION,
  TEXT_BASIC,
  TEXT_VALIDATION,
  TRANSLATIONS,
  getValidationEditForm,
} from './edit/tabs';

class TextField extends Formio.Components.components.textfield {
  static editForm() {
    return {
      components: [
        {
          type: 'tabs',
          key: 'tabs',
          components: [
            TEXT_BASIC,
            LOCATION,
            ADVANCED,
            getValidationEditForm(TEXT_VALIDATION),
            REGISTRATION,
            PREFILL,
            TRANSLATIONS,
          ],
        },
      ],
    };
  }
}

export default TextField;
