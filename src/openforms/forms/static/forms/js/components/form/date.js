import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

const DateTimeField = Formio.Components.components.datetime;


class DateField extends DateTimeField {
    static schema(...extend) {
        return DateTimeField.schema({
            type: 'date',
            label: 'Date',
            key: 'date',
            format: "dd-MM-yyyy",
            enableTime: false,
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Date Field',
            icon: 'fa fa-calendar',
            group: 'basic',
            weight: 10,
            schema: DateField.schema(),
        };
    }

    get defaultSchema() {
        return DateField.schema();
    }

}

defineCommonEditFormTabs(DateField);

export default DateField;
