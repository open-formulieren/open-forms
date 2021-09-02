import {Formio} from "formiojs";
import DEFAULT_TABS, {BASIC, ADVANCED, REGISTRATION, VALIDATION} from "./edit/tabs";

const DateTimeField = Formio.Components.components.datetime;

const APPOINTMENT = {
    key: 'appointment',
    label: 'Appointment',
    components: [
        {
            type: 'checkbox',
            key: 'appointmentsBirthDate',
            label: 'Birth Date for Appointment',
            tooltip: 'The value filled into this component will be used as the birth date for booking the appointment'
        }
    ]
};


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
        const TABS = {
            ...DEFAULT_TABS,
            components: [
                BASIC,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
                APPOINTMENT
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
