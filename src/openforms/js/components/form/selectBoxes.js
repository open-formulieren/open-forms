import {Formio} from 'formiojs';
import {DEFAULT_CHOICES_TABS} from "./edit/tabs";


class SelectBoxesField extends Formio.Components.components.selectboxes {
    static editForm() {
        return {components: [DEFAULT_CHOICES_TABS]};
    }
}

export default SelectBoxesField;
