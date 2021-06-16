import {Formio} from 'formiojs';
import {defineCommonEditFormTabs} from './abstract';


const DateTime = Formio.Components.components.datetime;
defineCommonEditFormTabs(DateTime);

/**
 * Here the formio datetime field is used as the base because I couldn't get the time field to
 * work properly with the 24h format. So the CalendarWidget is used, where the date input is disabled.
 */
class Time24hField extends DateTime {
    static schema(...extend) {
        return DateTime.schema({
            type: 'time24h',
            label: 'Time',
            key: 'time24h',
            format: 'HH:mm',
            useLocaleSettings: false,
            allowInput: true,
            enableDate: false,
            enableTime: true,
            defaultValue: '',
            defaultDate: '',
            displayInTimezone: 'viewer',
            timezone: '',
            datepickerMode: 'day',
            datePicker: {
                showWeeks: true,
                startingDay: 0,
                initDate: '',
                minMode: 'day',
                maxMode: 'year',
                yearRows: 4,
                yearColumns: 5,
                minDate: null,
                maxDate: null
            },
            timePicker: {
                hourStep: 1,
                minuteStep: 1,
                showMeridian: false,
                readonlyInput: false,
                mousewheel: true,
                arrowkeys: true
            },
        customOptions: {},
    }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Time',
            icon: 'clock-o',
            group: 'basic',
            weight: 10,
            schema: Time24hField.schema(),
        };
    }

    get defaultSchema() {
        return Time24hField.schema();
    }
}

Formio.registerComponent('time24h', Time24hField);

export default Time24hField;
