import {Formio} from 'formiojs';
import {DEFAULT_CHOICES_TABS} from "./edit/tabs";


class RadioField extends Formio.Components.components.radio {
    static editForm() {
        return {components: [DEFAULT_CHOICES_TABS]};
    }
}

export default RadioField;
