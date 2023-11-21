import {Formio} from 'formiojs';

import {CHOICES_BASIC, DEFAULT_CHOICES_TABS, TRANSLATIONS} from './edit/tabs';
import {localiseSchema} from './i18n';

const SelectBoxes = Formio.Components.components.selectboxes;

class SelectBoxesField extends SelectBoxes {
  static schema(...extend) {
    const schema = SelectBoxes.schema(
      {
        openForms: {dataSrc: 'manual'},
        values: [{value: '', label: ''}],
        defaultValue: {},
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      ...SelectBoxes.builderInfo,
      schema: SelectBoxesField.schema(),
    };
  }
  static editForm() {
    const choicesBasic = {
      key: 'basic',
      label: 'Basic',
      components: [...CHOICES_BASIC.components.filter(component => component.key !== 'multiple')],
    };
    let defaultChoicesTabs = {...DEFAULT_CHOICES_TABS};
    defaultChoicesTabs.components[0] = choicesBasic;
    if (!defaultChoicesTabs.components.includes(TRANSLATIONS))
      defaultChoicesTabs.components.push(TRANSLATIONS);

    return {components: [defaultChoicesTabs]};
  }

  setSelectedClasses() {
    // In the case the source is a variable, the input.value can be null in the form editor for the default value component
    if (this.dataValue === null) return;

    return super.setSelectedClasses();
  }
}

export default SelectBoxesField;
