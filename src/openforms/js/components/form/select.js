import {Formio} from 'formiojs';
import {getContextComponentsWithType} from '../../utils/helpers';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from './edit/tabs';

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
            key: 'appointmentsShowProducts',
            label: 'Show Products',
            tooltip: 'Show products the user can book in this component'
        },
        {
            type: 'checkbox',
            key: 'appointmentsShowLocations',
            label: 'Show Locations',
            tooltip: 'Show locations for a given product in this component'
        },
        {
            type: 'select',
            input: true,
            label: 'Select product component for locations',
            key: 'appointmentsProductForLocations',
            dataSrc: 'custom',
            tooltip: 'Choose the product component and we wil prefill locations for that product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return getContextComponentsWithType(context, 'select');
                }
            }
        },
        {
            type: 'checkbox',
            key: 'appointmentsShowDates',
            label: 'Show Dates',
            tooltip: 'Show dates for a given product at a given location'
        },
        {
            type: 'select',
            input: true,
            label: 'Select product component for dates',
            key: 'appointmentsProductForDates',
            dataSrc: 'custom',
            tooltip: 'Choose the product component and we wil prefill dates for that product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return getContextComponentsWithType(context, 'select');
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'Select location component for dates',
            key: 'appointmentsLocationForDates',
            dataSrc: 'custom',
            tooltip: 'Choose the location component and we wil prefill dates for the location and product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return getContextComponentsWithType(context, 'select');
                }
            }
        },
        {
            type: 'checkbox',
            key: 'appointmentsShowTimes',
            label: 'Show Times',
            tooltip: 'Show times for a given product, location, and date'
        },
        {
            type: 'select',
            input: true,
            label: 'Select product component for times',
            key: 'appointmentsProductForTimes',
            dataSrc: 'custom',
            tooltip: 'Choose the product component and we wil prefill times for that product in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return getContextComponentsWithType(context, 'select');
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'Select location component for times',
            key: 'appointmentsLocationForTimes',
            dataSrc: 'custom',
            tooltip: 'Choose the location component and we wil prefill times for that location in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return getContextComponentsWithType(context, 'select');
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'Select date component for times',
            key: 'appointmentsDateForTimes',
            dataSrc: 'custom',
            tooltip: 'Choose the date component and we wil prefill times for that date in this component',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return getContextComponentsWithType(context, 'select');
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
