import {Formio} from 'react-formio';

import {DEFAULT_VALUE, MULTIPLE} from './edit/options';
import {SENSITIVE_BASIC, DEFAULT_SENSITIVE_TABS} from './edit/tabs';

class SignatureField extends Formio.Components.components.signature {
    static editForm() {
        const exclude = [DEFAULT_VALUE.key, MULTIPLE.key];
        const choicesSensitiveBasic = {
            key: 'basic',
            label: 'Basic',
            components: [
                ...SENSITIVE_BASIC.components.filter(component => !exclude.includes(component.key)),
            ]
        };
        let defaultSensitiveTabs = {...DEFAULT_SENSITIVE_TABS};
        defaultSensitiveTabs.components[0] = choicesSensitiveBasic;

        return {components: [defaultSensitiveTabs]};
    }

}

export default SignatureField;
