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

defineCommonEditFormTabs(Formio.Components.components.textarea);


export default TextField;
