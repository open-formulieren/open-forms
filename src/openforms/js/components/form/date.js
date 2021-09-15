import {Formio} from "formiojs";
import DEFAULT_TABS, {BASIC, ADVANCED, REGISTRATION, VALIDATION, DEFAULT_TEXT_TABS} from "./edit/tabs";

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
        return {components: [DEFAULT_TABS]};
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
