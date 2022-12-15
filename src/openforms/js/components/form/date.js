import {Formio} from 'formiojs';
import {
  DEFAULT_TABS,
  ADVANCED,
  REGISTRATION,
  SENSITIVE_READ_ONLY,
  VALIDATION,
  PREFILL,
  TRANSLATIONS,
} from './edit/tabs';

const DateTimeField = Formio.Components.components.datetime;

const MESSAGES = {
  panel: {
    minDate: 'Minimum Date',
    maxDate: 'Maximum Date',
  },
  fixedValueLabel: {
    minDate: 'Minimum Date',
    maxDate: 'Maximum Date',
  },
  fixedValueTooltip: {
    minDate: 'The minimum date that can be picked.',
    maxDate: 'The maximum date that can be picked.',
  },
};

const getMinMaxValidationEditForm = fieldName => {
  const panel = {
    type: 'panel',
    key: `openForms.${fieldName}`,
    title: MESSAGES.panel[fieldName],
    components: [
      {
        type: 'select',
        key: `openForms.${fieldName}.mode`,
        label: 'Mode preset',
        defaultValue: 'fixedValue',
        data: {
          values: [
            {
              label: 'Fixed value',
              value: 'fixedValue',
            },
            fieldName === 'minDate' && {
              label: 'In the future',
              value: 'future',
            },
            fieldName === 'maxDate' && {
              label: 'In the past',
              value: 'past',
            },
            {
              label: 'Relative to variable',
              value: 'relativeToVariable',
            },
          ].filter(Boolean),
        },
      },
      {
        type: 'datetime',
        input: true,
        enableTime: false,
        key: `datePicker.${fieldName}`,
        label: MESSAGES.fixedValueLabel[fieldName],
        weight: 10,
        tooltip: MESSAGES.fixedValueTooltip[fieldName],
        clearOnHide: true,
        customConditional({data, component}) {
          if (
            component.datePicker &&
            component.datePicker[fieldName] &&
            component.datePicker[fieldName].indexOf('moment') !== -1
          ) {
            return false;
          }
          const upperCasedFieldName = fieldName.charAt(0).toUpperCase() + fieldName.substring(1);
          const attrName = `enable${upperCasedFieldName}Input`;
          const isFixedValue = data?.openForms[fieldName]?.mode === 'fixedValue';
          return isFixedValue && !data[attrName];
        },
      },
      {
        type: 'checkbox',
        key: `openForms.${fieldName}.includeToday`,
        label: 'Including today',
        tooltip: 'If checked, the current day is an allowed value.',
        conditional: {
          json: {
            in: [{var: `data.openForms.${fieldName}.mode`}, ['future', 'past']],
          },
        },
        defaultValue: false,
      },
      {
        type: 'columns',
        key: `openForms.${fieldName}.relative`,
        label: 'Relative to',
        clearOnHide: true,
        conditional: {
          show: true,
          when: `openForms.${fieldName}.mode`,
          eq: 'relativeToVariable',
        },
        columns: [
          {
            size: '6',
            components: [
              {
                type: 'select',
                key: `openForms.${fieldName}.operator`,
                label: 'Add/subtract duration',
                tooltip: 'Specify whether to add or subtract a time delta to/from the variable',
                defaultValue: 'add',
                data: {
                  values: [
                    {
                      label: 'Add duration',
                      value: 'add',
                    },
                    {
                      label: 'Subtract',
                      value: 'subtract',
                    },
                  ],
                },
              },
            ],
          },
          {
            size: '6',
            components: [
              {
                type: 'textfield',
                key: `openForms.${fieldName}.variable`,
                defaultValue: 'now',
                clearOnHide: true,
                label: 'Variable',
                tooltip: 'Provide the key of a static, component, or user defined variable.',
              },
            ],
          },
        ],
      },
      {
        type: 'columns',
        key: `openForms.${fieldName}.delta`,
        label: 'Delta configuration',
        clearOnHide: true,
        conditional: {
          show: true,
          when: `openForms.${fieldName}.mode`,
          eq: 'relativeToVariable',
        },
        columns: [
          {
            size: '4',
            components: [
              {
                type: 'number',
                key: 'years',
                label: 'Years',
                tooltip: 'Number of years. Empty values are ignored.',
                validate: {
                  min: 0,
                },
              },
            ],
          },
          {
            size: '4',
            components: [
              {
                type: 'number',
                key: 'months',
                label: 'Months',
                tooltip: 'Number of months. Empty values are ignored.',
                validate: {
                  min: 0,
                },
              },
            ],
          },
          {
            size: '4',
            components: [
              {
                type: 'number',
                key: 'days',
                label: 'Days',
                tooltip: 'Number of days. Empty values are ignored.',
                validate: {
                  min: 0,
                },
              },
            ],
          },
        ],
      },
    ],
  };
  return panel;
};

class DateField extends DateTimeField {
  static schema(...extend) {
    return DateTimeField.schema(
      {
        type: 'date',
        label: 'Date',
        key: 'date',
        format: 'dd-MM-yyyy',
        placeholder: 'dd-mm-yyyy',
        enableTime: false,
        // Open Forms extension options - we process those on the backend to set an
        // actual, calculated `minDate`/`maxDate` value dynamically.
        openForms: {
          minDate: {
            mode: 'fixedValue',
            // options for future/past mode
            includeToday: null,
            // options for relativeToVariable mode
            operator: 'add',
            variable: 'now',
            delta: {
              years: null,
              months: null,
              days: null,
            },
          },
          maxDate: {
            mode: 'fixedValue',
            // options for future/past mode
            includeToday: null,
            // options for relativeToVariable mode
            operator: 'add',
            variable: 'now',
            delta: {
              years: null,
              months: null,
              days: null,
            },
          },
        },
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'Date Field',
      icon: 'calendar',
      group: 'basic',
      weight: 10,
      schema: DateField.schema(),
    };
  }

  static editForm() {
    const VALIDATION_TAB = {
      ...VALIDATION,
      components: [
        ...VALIDATION.components,
        getMinMaxValidationEditForm('minDate'),
        getMinMaxValidationEditForm('maxDate'),
      ],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [
        SENSITIVE_READ_ONLY,
        ADVANCED,
        VALIDATION_TAB,
        REGISTRATION,
        PREFILL,
        TRANSLATIONS,
      ],
    };
    return {components: [TABS]};
  }

  get suffix() {
    // Don't show an icon
    return null;
  }

  get defaultSchema() {
    return DateField.schema();
  }

  constructor(component, options, data) {
    super(component, options, data);

    // These fields get automatically added to the configuration in the builder, and their value is `undefined`.
    // For some reason, their value is then not saved in the backend. So, when comparing the configuration with the
    // saved configuration (useDetectConfigurationChanged), they look different and cause a warning that the
    // configuration has changed.
    // By giving them a value when first build, then the values are saved in the backend. (Github #1255)
    this.component.widget = {
      ...this.component.widget,
      disabledDates: null,
      disableWeekends: null,
      disableWeekdays: null,
      disableFunction: null,
      readOnly: false,
      submissionTimezone: null,
      timezone: '',
    };
  }
}

export default DateField;
