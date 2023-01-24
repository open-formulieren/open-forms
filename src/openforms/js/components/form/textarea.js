import {Formio} from 'react-formio';

import {ADVANCED, TEXT_BASIC, TEXT_VALIDATION, TRANSLATIONS} from './edit/tabs';
import {localiseSchema} from './i18n';

const textareaBasicTab = {
  key: 'basic',
  label: 'Basic',
  components: [
    ...TEXT_BASIC.components,
    {
      type: 'checkbox',
      input: true,
      key: 'autoExpand',
      label: 'Auto Expand',
      tooltip:
        "This will make the TextArea auto expand it's height as the user is typing into the area.",
      weight: 415,
      conditional: {
        json: {
          '==': [{var: 'data.editor'}, ''],
        },
      },
    },
    {
      type: 'number',
      input: true,
      weight: 80,
      key: 'rows',
      label: 'Number of rows',
      tooltip: 'The number of rows for this text area.',
    },
  ],
};

const textareaTabs = {
  type: 'tabs',
  key: 'tabs',
  components: [textareaBasicTab, ADVANCED, TEXT_VALIDATION, TRANSLATIONS],
};

const FormioTextarea = Formio.Components.components.textarea;

class TextArea extends FormioTextarea {
  static schema(...extend) {
    return localiseSchema(FormioTextarea.schema({validate: {maxLength: 10000}}, ...extend));
  }

  static get builderInfo() {
    return {
      ...FormioTextarea.builderInfo,
      schema: TextArea.schema(),
    };
  }

  get defaultSchema() {
    return TextArea.schema();
  }

  static editForm() {
    return {components: [textareaTabs]};
  }
}

export default TextArea;
