import {Formio} from 'react-formio';

import {SENSITIVE_BASIC, DEFAULT_SENSITIVE_TABS} from './edit/tabs';

class SignatureField extends Formio.Components.components.signature {
    static editForm() {
        const choicesSensitiveBasic = {
            key: 'basic',
            label: 'Basic',
            components: [
                ...SENSITIVE_BASIC.components.filter(component => component.key !== 'multiple'),
            ]
        };
        let defaultSensitiveTabs = {...DEFAULT_SENSITIVE_TABS};
        defaultSensitiveTabs.components[0] = choicesSensitiveBasic;

        return {components: [defaultSensitiveTabs]};
    }

}

export default SignatureField;
