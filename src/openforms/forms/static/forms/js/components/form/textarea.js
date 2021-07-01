import {Formio} from 'react-formio';

import {ADVANCED, TEXT_BASIC, TEXT_VALIDATION} from './edit/tabs';


const TextAreaBasicTab = {
    key: 'basic',
    label: 'Basic',
    components: [
        ...TEXT_BASIC.components,
        {
            type: 'checkbox',
            input: true,
            key: 'autoExpand',
            label: 'Auto Expand',
            tooltip: 'This will make the TextArea auto expand it\'s height as the user is typing into the area.',
            weight: 415,
            conditional: {
                json: {
                    '==': [
                        {var: 'data.editor'},
                        ''
                    ]
                }
            }
        },
        {
            type: 'number',
            input: true,
            weight: 80,
            key: 'rows',
            label: 'Number of rows',
            tooltip: 'The number of rows for this text area.'
        }
    ]
};


const TextAreaTabs = {
    type: 'tabs',
    key: 'tabs',
    components: [
        TextAreaBasicTab,
        ADVANCED,
        TEXT_VALIDATION,
    ]
};


class TextArea extends Formio.Components.components.textarea {

    static editForm() {
        return {components: [TextAreaTabs]};
    }

}

export default TextArea;
