import {Formio} from 'formiojs';

import {HIDDEN, KEY, LABEL, PRESENTATION, SHOW_IN_EMAIL, SHOW_IN_PDF} from './edit/options';
import {ADVANCED, LANGUAGES, TRANSLATIONS} from './edit/tabs';

const FormioContentField = Formio.Components.components.content;

const CUSTOM_CSS_CLASS = {
  weight: 500,
  type: 'select',
  input: true,
  label: 'Custom CSS Class',
  key: 'customClass',
  data: {
    values: [
      {label: 'Warning', value: 'warning'},
      {label: 'Info', value: 'info'},
      {label: 'Error', value: 'error'},
      {label: 'Success', value: 'success'},
    ],
  },
};

const CONTENT_PRESENTATION = {
  ...PRESENTATION,
  components: [SHOW_IN_EMAIL, SHOW_IN_PDF],
};

const CONTENT_EDITOR = {
  weight: 0,
  type: 'textarea',
  editor: 'ckeditor',
  label: 'Content',
  hideLabel: true,
  input: true,
  key: 'html',
  as: 'html',
  rows: 3,
  tooltip: 'The HTML template for the result data items.',
};

const CONTENT_EDIT_TABS = {
  components: [
    {
      type: 'columns',
      key: 'content',
      columns: [
        {
          components: [
            {
              type: 'tabs',
              components: [{label: 'Content', components: [CONTENT_EDITOR]}],
            },
          ],
        },
        {
          components: [
            {
              ...TRANSLATIONS,
              hideLabel: true,
              components: [
                {
                  key: 'languages',
                  type: 'tabs',
                  components: LANGUAGES.map(([languageCode, _label]) => {
                    return {
                      key: languageCode,
                      label: languageCode.toUpperCase(),
                      components: [
                        {
                          label: 'Literal',
                          hideLabel: true,
                          key: `of-translations.${languageCode}[0].literal`,
                          input: true,
                          unique: true,
                          type: 'hidden',
                          customDefaultValue: ({instance, data}) =>
                            instance.options.editComponent.html,
                        },
                        {
                          label: 'Translation',
                          hideLabel: true,
                          key: `of-translations.${languageCode}[0].translation`,
                          customDefaultValue: ({instance, data}) =>
                            instance.options.componentTranslations.current[languageCode][
                              instance.options.editComponent.html
                            ],
                          input: true,
                          type: 'textarea',
                          editor: 'ckeditor',
                          as: 'html',
                          rows: 3,
                        },
                      ],
                    };
                  }),
                },
              ],
            },
          ],
        },
      ],
    },
    {
      type: 'tabs',
      key: 'tabs',
      components: [
        {
          label: 'Display',
          key: 'display',
          weight: 0,
          components: [LABEL, KEY, HIDDEN, CONTENT_PRESENTATION, CUSTOM_CSS_CLASS],
        },
        ADVANCED,
      ],
    },
  ],
};

class ContentField extends FormioContentField {
  static editForm() {
    return CONTENT_EDIT_TABS;
  }
}

export default ContentField;
