import {Formio} from 'formiojs';

import {MULTIPLE} from './edit/options';
import {
    DEFAULT_CHOICES_TABS,
    CHOICES_BASIC,
    ADVANCED,
    VALIDATION,
    REGISTRATION,
} from './edit/tabs';


class RadioField extends Formio.Components.components.radio {
    static editForm() {
        return {components: [
            {
                ...DEFAULT_CHOICES_TABS,
                components: [
                    {
                        ...CHOICES_BASIC,
                        components: CHOICES_BASIC.components.filter(option => option.key !== MULTIPLE.key),
                    },
                    ADVANCED,
                    VALIDATION,
                    REGISTRATION,
                ],
            }
        ]};
    }
}

export default RadioField;
