import {Formio} from 'formiojs';

import {getMinMaxValidationEditForm} from './edit/date-edit-form';
import {
  ADVANCED,
  DEFAULT_TABS,
  PREFILL,
  REGISTRATION,
  SENSITIVE_READ_ONLY,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';
import {localiseSchema} from './i18n';

const DateTimeFormio = Formio.Components.components.datetime;

class DateTimeField extends DateTimeFormio {
  static schema(...extend) {
    const schema = DateTimeFormio.schema(
      {
        type: 'datetime',
        label: 'Date / Time',
        key: 'dateTime',
        format: 'dd-MM-yyyy HH:mm',
        placeholder: 'dd-MM-yyyy HH:mm',
        enableTime: true,
        time_24hr: true,
        timePicker: {
          hourStep: 1,
          minuteStep: 1,
          showMeridian: false,
          readonlyInput: false,
          mousewheel: true,
          arrowkeys: true,
        },
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
          // Issue #3755 - Flatpickr is preventing the value from being set when entering it manually if it is outside the set minDate/maxDate range.
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
      title: 'Date / Time',
      icon: 'calendar-plus',
      group: 'basic',
      weight: 10,
      schema: DateTimeField.schema(),
    };
  }

  static editForm() {
    const VALIDATION_TAB = {
      ...VALIDATION,
      components: [
        ...VALIDATION.components,
        getMinMaxValidationEditForm('minDate', 'datetime'),
        getMinMaxValidationEditForm('maxDate', 'datetime'),
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
    return DateTimeField.schema();
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

export default DateTimeField;
