import {Formio, Utils} from 'formiojs';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from "./edit/tabs";
import {getFullyQualifiedUrl} from "../../utils/urls";

const Select = Formio.Components.components.select;

const values = [{
    type: 'datagrid',
    input: true,
    label: 'Values',
    key: 'data.values',
    tooltip: 'The radio button values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
    weight: 10,
    reorder: true,
    defaultValue: [{label: '', value: ''}],
    components: [
        {
            label: 'Label',
            key: 'label',
            input: true,
            type: 'textfield',
        },
        {
            label: 'Value',
            key: 'value',
            input: true,
            type: 'textfield',
            allowCalculateOverride: true,
            calculateValue: {_camelCase: [{var: 'row.label'}]},
        },
    ],
}];

const APPOINTMENT = {
    key: 'appointment',
    label: 'Appointment',
    components: [
        {
            type: 'checkbox',
            key: 'showProducts',
            label: 'Show Products',
            tooltip: 'Show products the user can book in this component'
        },
        {
            type: 'checkbox',
            key: 'showLocations',
            label: 'Show Locations',
            tooltip: 'Show locations for a given product in this component'
        },
        {
            type: 'select',
            input: true,
            label: 'Select product component for locations',
            key: 'productForLocations',
            dataSrc: 'custom',
            tooltip: 'Choose the product component and we wil prefill locations for that product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        },
        {
            type: 'checkbox',
            key: 'showDates',
            label: 'Show Dates',
            tooltip: 'Show dates for a given product at a given location'
        },
        {
            type: 'select',
            input: true,
            label: 'Select product component for dates',
            key: 'productForDates',
            dataSrc: 'custom',
            tooltip: 'Choose the product component and we wil prefill dates for that product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'Select location component for dates',
            key: 'locationForDates',
            dataSrc: 'custom',
            tooltip: 'Choose the location component and we wil prefill dates for the location and product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        },
        {
            type: 'checkbox',
            key: 'showTimes',
            label: 'Show Times',
            tooltip: 'Show times for a given product, location, and date'
        },
        {
            type: 'select',
            input: true,
            label: 'Select product component for times',
            key: 'productForTimes',
            dataSrc: 'custom',
            tooltip: 'Choose the product component and we wil prefill times for that product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'Select location component for dates',
            key: 'locationForTimes',
            dataSrc: 'custom',
            tooltip: 'Choose the location component and we wil prefill times for that location in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'Select location component for dates',
            key: 'dateForTimes',
            dataSrc: 'custom',
            tooltip: 'Choose the date component and we wil prefill times for that date in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        }
    ]
};


class SelectField extends Select {

    static editForm() {
        const BASIC_TAB = {
            ...BASIC,
            components: [
                ...BASIC.components,
                ...values,
            ]
        };
        const TABS = {
            ...DEFAULT_TABS,
            components: [
                BASIC_TAB,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
                APPOINTMENT
            ]
        };
        return {components: [TABS]};
    }
}

export default SelectField;
