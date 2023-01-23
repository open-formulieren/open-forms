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

const AUTOCOMPLETE_PASSWORD = {
  type: 'textfield',
  key: 'autocomplete',
  label: 'Autocomplete',
  placeholder: 'password',
  tooltip: 'Display options to fill in the field, based on earlier typed values.',
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

export {
  LABEL_REQUIRED,
  LABEL,
  KEY,
  DESCRIPTION,
  SHOW_IN_SUMMARY,
  SHOW_IN_EMAIL,
  SHOW_IN_PDF,
  AUTOCOMPLETE,
  AUTOCOMPLETE_PASSWORD,
  PRESENTATION,
  MULTIPLE,
  HIDDEN,
  CLEAR_ON_HIDE,
  IS_SENSITIVE_DATA,
  DEFAULT_VALUE,
  READ_ONLY,
  REGEX_VALIDATION,
  REQUIRED,
};
