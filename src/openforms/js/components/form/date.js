import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const DateTimeField = Formio.Components.components.datetime;

class DateField extends DateTimeField {
  static schema(...extend) {
    const schema = DateTimeField.schema(
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
            mode: '',
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
            mode: '',
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
        customOptions: {
          // Issue #3443 - Flatpickr is preventing the value from being set when entering it manually if it is outside the set minDate/maxDate range.
          // With allowInvalidPreload: true, we tell it to set the value also if it is invalid, so that then validators can kick in.
          // https://github.com/flatpickr/flatpickr/blob/master/src/index.ts#L2498
          allowInvalidPreload: true,
        },
      },
      ...extend
    );
    return localiseSchema(schema);
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
