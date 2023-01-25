import {Formio} from 'formiojs';

import {MULTIPLE} from './edit/options';
import {ADVANCED, BASIC, DEFAULT_TABS, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';

const Checkbox = Formio.Components.components.checkbox;

class CheckboxField extends Checkbox {
  static schema(...extend) {
    return localiseSchema(Checkbox.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...Checkbox.builderInfo,
      schema: CheckboxField.schema(),
    };
  }

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
