import {Formio} from 'react-formio';
import {defineCommonEditFormTabs} from './abstract';

import DEFAULT_TABS, { PREFILL } from './edit/tabs';


class TextField extends Formio.Components.components.textfield {

    static editForm() {
        const tabs = {
            ...DEFAULT_TABS,
            components: [
                ...DEFAULT_TABS.components,
                PREFILL,
            ]
        }
        return {components: [tabs]};
    }

}

const rows = {
    type: 'number',
    input: true,
    weight: 80,
    key: 'rows',
    label: 'Number of rows',
    tooltip: 'The number of rows for this text area.'
};

defineCommonEditFormTabs(Formio.Components.components.textarea, [rows]);

export default TextField;
