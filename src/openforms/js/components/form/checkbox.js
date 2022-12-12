import {Formio} from 'formiojs';

import {MULTIPLE} from './edit/options';
import {DEFAULT_TABS, BASIC, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS} from './edit/tabs';

class CheckboxField extends Formio.Components.components.checkbox {
  static editForm() {
    return {
      components: [
        {
          ...DEFAULT_TABS,
          components: [
            {
              ...BASIC,
              components: BASIC.components.filter(option => option.key !== MULTIPLE.key),
            },
            ADVANCED,
            VALIDATION,
            REGISTRATION,
            TRANSLATIONS,
          ],
        },
      ],
    };
  }
}

export default CheckboxField;
