import {Formio} from 'formiojs';

import {DEFAULT_CHOICES_TABS, CHOICES_BASIC, TRANSLATIONS} from './edit/tabs';

class SelectBoxesField extends Formio.Components.components.selectboxes {
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
}

export default SelectBoxesField;
