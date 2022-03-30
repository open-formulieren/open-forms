import {Formio} from 'formiojs';
import {DEFAULT_TABS, ADVANCED, REGISTRATION, SENSITIVE_READ_ONLY, VALIDATION, PREFILL} from './edit/tabs';

const DateTimeField = Formio.Components.components.datetime;

class DateField extends DateTimeField {
    static schema(...extend) {
        return DateTimeField.schema({
            type: 'date',
            label: 'Date',
            key: 'date',
            format: 'dd-MM-yyyy',
            placeholder: 'dd-mm-yyyy',
            enableTime: false,
        }, ...extend);
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
        const extra = [
            {
                type: 'datetime',
                input: true,
                enableTime: false,
                key: 'datePicker.minDate',
                label: 'Minimum Date',
                weight: 10,
                tooltip: 'The minimum date that can be picked.',
                customConditional({ data, component }) {
                    if (component.datePicker && component.datePicker.minDate && component.datePicker.minDate.indexOf('moment') !== -1) {
                        return false;
                    }
                    return !data.enableMinDateInput;
                },
            },
            {
                type: 'datetime',
                input: true,
                enableTime: false,
                key: 'datePicker.maxDate',
                label: 'Maximum Date',
                tooltip: 'The maximum date that can be picked.',
                weight: 10,
                customConditional({ data, component }) {
                    if (component.datePicker && component.datePicker.maxDate && component.datePicker.maxDate.indexOf('moment') !== -1) {
                        return false;
                    }
                    return !data.enableMaxDateInput;
                },
            }
        ];

        const BASIC_TAB = {
            ...SENSITIVE_READ_ONLY,
            components: [
                ...SENSITIVE_READ_ONLY.components,
                ...extra,
            ]
        };
        const TABS = {
            ...DEFAULT_TABS,
            components: [
                BASIC_TAB,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
                PREFILL,
            ]
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
