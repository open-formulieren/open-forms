import {Formio} from 'formiojs';
import cloneDeep from 'lodash/cloneDeep';

import {
  CLEAR_ON_HIDE,
  DESCRIPTION,
  HIDDEN,
  IS_SENSITIVE_DATA,
  KEY,
  LABEL_REQUIRED,
  MULTIPLE,
  OPTIONS_CHOICES,
  PRESENTATION,
  TOOLTIP,
} from './edit/options';
import DEFAULT_TABS, {ADVANCED, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';

const Select = Formio.Components.components.select;

const getOptionsChoices = () => {
  let selectOptionsChoices = cloneDeep(OPTIONS_CHOICES);
  if (selectOptionsChoices[1].key !== 'values') {
    throw new Error(
      `Expected the second component to be "values", has ${selectOptionsChoices[1].key}`
    );
  }
  // For radio and selectboxes components, the values have key 'values'. For select, it's 'data.values'
  selectOptionsChoices[1].key = 'data.values';
  return selectOptionsChoices;
};

class SelectField extends Select {
  static schema(...extend) {
    const schema = Select.schema(
      {
        openForms: {dataSrc: 'manual'},
        values: [{value: '', label: ''}],
        defaultValue: '',
      },
      ...extend
    );
    return localiseSchema({...schema, key: 'select-key'});
  }

  static get builderInfo() {
    return {
      ...Select.builderInfo,
      schema: SelectField.schema(),
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
        MULTIPLE,
        HIDDEN,
        CLEAR_ON_HIDE,
        IS_SENSITIVE_DATA,
        ...getOptionsChoices(),
      ],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default SelectField;
