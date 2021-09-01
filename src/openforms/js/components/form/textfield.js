import {Formio} from 'react-formio';

import {DEFAULT_TEXT_TABS, PREFILL} from './edit/tabs';

const APPOINTMENT = {
    key: 'appointment',
    label: 'Appointment',
    components: [
        {
            type: 'checkbox',
            key: 'appointments.appointmentLastName',
            label: 'Last Name for Appointment',
            tooltip: 'The value filled into this component will be used as the last name for booking the appointment'
        }
    ]
};



class TextField extends Formio.Components.components.textfield {

    static editForm() {
        const tabs = {
            ...DEFAULT_TEXT_TABS,
            components: [
                ...DEFAULT_TEXT_TABS.components,
                PREFILL,
                APPOINTMENT,
            ]
        };
        return {components: [tabs]};
    }

}

export default TextField;
