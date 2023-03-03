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

const getMinMaxValidationEditForm = (fieldName, componentType) => {
  const namespace = `openForms.${fieldName}`;
  const panel = {
    type: 'panel',
    key: `${fieldName}ValidationPanel`,
    title: MESSAGES.panel[fieldName],
    components: [
      {
        type: 'select',
        key: `${namespace}.mode`,
        label: 'Mode preset',
        defaultValue: '',
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
          return data?.openForms?.[fieldName]?.mode === 'fixedValue';
        },
      },
      // Only include 'includingToday' for dates, since it doesn't make sense for datetimes when checking if a
      // datetime is in the past/future
      componentType === 'date' && {
        type: 'checkbox',
        key: `${namespace}.includeToday`,
        label: 'Including today',
        tooltip: 'If checked, the current day is an allowed value.',
        conditional: {
          json: {
            in: [{var: `data.${namespace}.mode`}, ['future', 'past']],
          },
        },
        defaultValue: false,
      },
      {
        type: 'columns',
        key: `${fieldName}ValidationRelativeColumns`,
        label: 'Relative to',
        clearOnHide: true,
        conditional: {
          show: true,
          when: `${namespace}.mode`,
          eq: 'relativeToVariable',
        },
        columns: [
          {
            size: '6',
            components: [
              {
                type: 'select',
                key: `${namespace}.operator`,
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
                key: `${namespace}.variable`,
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
        key: `${fieldName}ValidationDeltaColumns`,
        label: 'Delta configuration',
        clearOnHide: true,
        conditional: {
          show: true,
          when: `${namespace}.mode`,
          eq: 'relativeToVariable',
        },
        columns: [
          {
            size: '4',
            components: [
              {
                type: 'number',
                key: `${namespace}.delta.years`,
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
                key: `${namespace}.delta.months`,
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
                key: `${namespace}.delta.days`,
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
    ].filter(Boolean),
  };
  return panel;
};

export {getMinMaxValidationEditForm};
