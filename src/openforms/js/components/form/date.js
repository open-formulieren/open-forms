import {Formio} from 'formiojs';
import {DEFAULT_TABS, ADVANCED, REGISTRATION, SENSITIVE_BASIC, VALIDATION} from './edit/tabs';

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
            ...SENSITIVE_BASIC,
            components: [
                ...SENSITIVE_BASIC.components,
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

}

export default DateField;
