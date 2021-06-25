import {Formio} from 'react-formio';

import DEFAULT_TABS from './edit/tabs';

class SignatureField extends Formio.Components.components.signature {
    static editForm() {
        return {components: [DEFAULT_TABS]};
    }

}

export default SignatureField;
