import {Formio} from 'react-formio';

import {
    DEFAULT_SENSITIVE_TABS,
    SENSITIVE_BASIC,
    ADVANCED,
    VALIDATION,
    REGISTRATION,
} from './edit/tabs';
import {DEFAULT_VALUE} from './edit/options';


class PasswordField extends Formio.Components.components.password {

    static editForm() {
        return {components: [
            {
                ...DEFAULT_SENSITIVE_TABS,
                components: [
                    {
                        ...SENSITIVE_BASIC,
                        components: SENSITIVE_BASIC.components.filter(option => option.key !== DEFAULT_VALUE.key),
                    },
                    ADVANCED,
                    VALIDATION,
                    REGISTRATION,
                ]
            }
        ]};
    }

}

export default PasswordField;
