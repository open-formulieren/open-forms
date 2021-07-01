import {Formio} from 'react-formio';

import DEFAULT_TABS, { PREFILL } from './edit/tabs';


class TextField extends Formio.Components.components.textfield {

    static editForm() {
        const tabs = {
            ...DEFAULT_TABS,
            components: [
                ...DEFAULT_TABS.components,
                PREFILL,
            ]
        };
        return {components: [tabs]};
    }

}

export default TextField;
