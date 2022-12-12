import {Formio} from 'formiojs';
import {
  CLEAR_ON_HIDE,
  DESCRIPTION,
  HIDDEN,
  IS_SENSITIVE_DATA,
  KEY,
  LABEL_REQUIRED,
  REQUIRED,
} from './edit/options';
import {TRANSLATIONS} from './edit/tabs';

const EditGridFormio = Formio.Components.components.editgrid;

const GROUP_LABEL = {
  type: 'textfield',
  key: 'groupLabel',
  label: 'Group label',
  tooltip:
    'The label that will be shown above each repeating group in the ' +
    'summary page, the submission report and the confirmation email. ' +
    'The index of the item will be added next to it, i.e. if you enter ' +
    "'Item' it will be displayed as 'Item 1', 'Item 2', ...",
  defaultValue: 'Item',
};

const EDIT_FORM_TABS = [
  {
    type: 'tabs',
    key: 'tabs',
    components: [
      {
        key: 'basic',
        label: 'Basic',
        components: [
          LABEL_REQUIRED,
          KEY,
          GROUP_LABEL,
          DESCRIPTION,
          HIDDEN,
          CLEAR_ON_HIDE,
          IS_SENSITIVE_DATA,
        ],
      },
      {
        key: 'display',
        label: 'Display',
        components: [
          // this is broken in the frontend in current versions of Formio, see
          // https://github.com/formio/formio.js/issues/4620 and #2081
          // {
          //   type: 'checkbox',
          //   label: 'Open First Row when Empty',
          //   key: 'openWhenEmpty',
          //   tooltip:
          //     'Check this if you would like to open up the first row when the EditGrid is empty',
          //   weight: 1000,
          //   input: true,
          //   conditional: {
          //     json: {'!==': [{var: 'data.modal'}, true]},
          //   },
          // },
          {
            type: 'checkbox',
            label: 'Disable Adding / Removing Rows',
            key: 'disableAddingRemovingRows',
            tooltip: 'Check if you want to hide Add Another button and Remove Row button',
            weight: 1001,
            input: true,
            clearOnHide: false,
            calculateValue: 'value = data.disableAddingRemovingRows;',
          },
          {
            type: 'textfield',
            input: true,
            key: 'addAnother',
            label: 'Add Another Text',
            placeholder: 'Add Another',
            tooltip: 'Set the text of the Add Another button.',
          },
          {
            type: 'textfield',
            input: true,
            key: 'saveRow',
            label: 'Save Row Text',
            placeholder: 'Save',
            tooltip: 'Set the text of the Save Row button.',
          },
          {
            type: 'textfield',
            input: true,
            key: 'removeRow',
            label: 'Remove Row Text',
            placeholder: 'Remove',
            tooltip: 'Set the text of the remove Row button.',
          },
        ],
      },
      {
        key: 'validation',
        label: 'Validation',
        components: [
          REQUIRED,
          {
            key: 'validate.maxLength',
            label: 'Maximum Length',
            type: 'number',
            tooltip: 'The maximum length requirement this field must meet.',
            input: true,
          },
        ],
      },
      TRANSLATIONS,
    ],
  },
];

class EditGrid extends EditGridFormio {
  static schema(...extend) {
    return EditGridFormio.schema(
      {
        label: 'Repeating Group',
        key: 'repeatingGroup',
        hideLabel: false,
        inlineEdit: true,
      },
      ...extend
    );
  }
  static get builderInfo() {
    return {
      hideLabel: false,
      title: 'Repeating Group',
      icon: 'repeat',
      schema: EditGrid.schema(),
    };
  }

  static editForm() {
    return {components: EDIT_FORM_TABS};
  }
}

export default EditGrid;
