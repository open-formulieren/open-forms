import {Formio} from 'react-formio';

import { DEFAULT_SENSITIVE_TABS } from './edit/tabs';


class PasswordField extends Formio.Components.components.password {

    static editForm() {
        return {components: [DEFAULT_SENSITIVE_TABS]};
    }

}

export default PasswordField;
