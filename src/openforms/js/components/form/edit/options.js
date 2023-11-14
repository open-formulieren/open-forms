const LABEL = {
  type: 'textfield',
  key: 'label',
  label: 'Label',
};

const LABEL_REQUIRED = {
  type: 'textfield',
  key: 'label',
  label: 'Label',
  validate: {
    required: true,
  },
};

const KEY = {
  type: 'textfield',
  key: 'key',
  label: 'Property Name',
  validate: {
    required: true,
    pattern: '(\\w|\\w[\\w-.]*\\w)',
    patternMessage:
      'The property name must only contain alphanumeric characters, underscores, dots and dashes and should not be ended by dash or dot.',
  },
};

const DESCRIPTION = {
  type: 'textfield',
  key: 'description',
  label: 'Description',
};

const TOOLTIP = {
  type: 'textfield',
  key: 'tooltip',
  label: 'Tooltip',
};

const SHOW_IN_SUMMARY = {
  type: 'checkbox',
  key: 'showInSummary',
  label: 'Show in summary',
  tooltip: 'Whether to show this value in the submission summary',
  defaultValue: true,
};

const SHOW_IN_EMAIL = {
  type: 'checkbox',
  key: 'showInEmail',
  label: 'Show in email',
  tooltip: 'Whether to show this value in the confirmation email',
};

const SHOW_IN_PDF = {
  type: 'checkbox',
  key: 'showInPDF',
  label: 'Show in PDF',
  tooltip: 'Whether to show this value in the confirmation PDF',
  defaultValue: true,
};

const AUTOCOMPLETE = {
  type: 'textfield',
  key: 'autocomplete',
  label: 'Autocomplete',
  placeholder: 'on',
  tooltip: 'Display options to fill in the field, based on earlier typed values.',
};

const PRESENTATION = {
  type: 'panel',
  title: 'Display in summaries and confirmations',
  key: 'presentationConfig',
  components: [SHOW_IN_SUMMARY, SHOW_IN_EMAIL, SHOW_IN_PDF],
};

const MULTIPLE = {
  type: 'checkbox',
  key: 'multiple',
  label: 'Multiple values',
  tooltip: 'Are there multiple values possible for this field?',
};

const HIDDEN = {
  type: 'checkbox',
  key: 'hidden',
  label: 'Hidden',
  tooltip: 'Hide a field from the form.',
};

const CLEAR_ON_HIDE = {
  type: 'checkbox',
  key: 'clearOnHide',
  label: 'Clear on hide',
  tooltip:
    'Remove the value of this field from the submission if it is hidden. Note: the value of this field is then also not used in logic rules!',
};

const IS_SENSITIVE_DATA = {
  type: 'checkbox',
  key: 'isSensitiveData',
  label: 'Is Sensitive Data',
  tooltip:
    'The data entered in this component will be removed in accordance with the privacy settings.',
};

const DEFAULT_VALUE = {
  label: 'Default Value',
  key: 'defaultValue',
  tooltip: 'This will be the initial value for this field, before user interaction.',
  input: true,
};

const READ_ONLY = {
  // This doesn't work as in native HTML forms. Marking a field as 'disabled' only makes it read-only in the
  // UI, but the data is still sent to the backend.
  type: 'checkbox',
  label: 'Read only',
  tooltip: 'Make this component read only',
  key: 'disabled',
  input: true,
};

const MIMINUM_TIME = {
  type: 'time',
  input: true,
  key: 'validate.minTime',
  label: 'Minimum Time',
  weight: 10,
  tooltip: 'The minimum time that can be picked.',
};

const MAXIMUM_TIME = {
  type: 'time',
  input: true,
  key: 'validate.maxTime',
  label: 'Maximum Time',
  weight: 10,
  tooltip: 'The maximum time that can be picked.',
};

const REGEX_VALIDATION = {
  weight: 130,
  key: 'validate.pattern',
  label: 'Regular Expression Pattern',
  placeholder: 'Regular Expression Pattern',
  type: 'textfield',
  tooltip:
    'The regular expression pattern test that the field value must pass before the form can be submitted.',
  input: true,
};

const REQUIRED = {
  type: 'checkbox',
  input: true,
  label: 'Required',
  tooltip: 'A required field must be filled in before the form can be submitted.',
  key: 'validate.required',
};

const OPTIONS_CHOICES = [
  {
    type: 'select',
    key: 'openForms.dataSrc',
    label: 'Data source',
    description: 'What data to use for the options of this field.',
    defaultValue: 'manual',
    data: {
      values: [
        {
          label: 'Manually fill in',
          value: 'manual',
        },
        {
          label: 'Variable',
          value: 'variable',
        },
      ],
    },
    validate: {
      required: true,
    },
  },
  {
    type: 'datagrid',
    input: true,
    label: 'Values',
    key: 'values',
    tooltip:
      'The values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
    weight: 10,
    reorder: true,
    defaultValue: [{label: '', value: ''}],
    components: [
      {
        label: 'Label',
        key: 'label',
        input: true,
        type: 'textfield',
        // Needed to distinguish from the label of the component, since both have key 'label'.
        // Issue #1422
        isOptionLabel: true,
      },
      {
        label: 'Value',
        key: 'value',
        input: true,
        type: 'textfield',
        allowCalculateOverride: true,
        calculateValue: {_camelCase: [{var: 'row.label'}]},
        validate: {
          required: true,
        },
      },
    ],
    clearOnHide: true,
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'manual',
    },
  },
  // We can't have the default value nested deeper, because Formio WebformBuilder expects it as a first child of a tab.
  {
    label: 'Default Value',
    key: 'defaultValue',
    tooltip: 'This will be the initial value for this field, before user interaction.',
    input: true,
    clearOnHide: true,
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'manual',
    },
  },
  {
    label: 'Items expression',
    key: 'openForms.itemsExpression',
    type: 'textarea',
    tooltip:
      'A JSON logic expression returning a variable (of array type) whose items should be used as the options for this component.',
    editor: 'ace',
    as: 'json',
    // Documentation for editor settings: https://ajaxorg.github.io/ace-api-docs/interfaces/Ace.EditorOptions.html
    // but most of the settings don't seem to work.
    conditional: {
      show: true,
      when: 'openForms.dataSrc',
      eq: 'variable',
    },
    validate: {
      required: true,
      custom: 'valid = (typeof input == "object") && validateLogic(input, [["", ""]])',
    },
  },
];

export {
  LABEL_REQUIRED,
  LABEL,
  KEY,
  DESCRIPTION,
  TOOLTIP,
  OPTIONS_CHOICES,
  SHOW_IN_SUMMARY,
  SHOW_IN_EMAIL,
  SHOW_IN_PDF,
  AUTOCOMPLETE,
  PRESENTATION,
  MULTIPLE,
  MIMINUM_TIME,
  MAXIMUM_TIME,
  HIDDEN,
  CLEAR_ON_HIDE,
  IS_SENSITIVE_DATA,
  DEFAULT_VALUE,
  READ_ONLY,
  REGEX_VALIDATION,
  REQUIRED,
};
