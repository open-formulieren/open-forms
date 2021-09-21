import {Formio} from 'react-formio';

import {DEFAULT_SENSITIVE_TABS} from './edit/tabs';

class SignatureField extends Formio.Components.components.signature {
    static editForm() {
        return {components: [DEFAULT_SENSITIVE_TABS]};
    }

}

export default SignatureField;
