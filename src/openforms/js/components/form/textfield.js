import {Formio} from 'react-formio';

import {DEFAULT_TEXT_TABS} from './edit/tabs';


class TextField extends Formio.Components.components.textfield {

    static editForm() {
        return {components: [DEFAULT_TEXT_TABS]};
    }

}

export default TextField;
