import {Formio} from 'formiojs';
import {HIDDEN, KEY, LABEL} from './edit/options';
import {ADVANCED} from './edit/tabs';

const FormioContentField = Formio.Components.components.content;

// TODO to be changed in Issue #1541
const CUSTOM_CSS_CLASS = {
    weight: 500,
    type: 'textfield',
    input: true,
    key: 'customClass',
    label: 'Custom CSS Class',
    placeholder: 'Custom CSS Class',
    tooltip: 'Custom CSS class to add to this component.'
};

const CONTENT_EDIT_TABS = {
    components: [
        {
            weight: 0,
            type: 'textarea',
            editor: 'ckeditor',
            label: 'Content',
            hideLabel: true,
            input: true,
            key: 'html',
            as: 'html',
            rows: 3,
            tooltip: 'The HTML template for the result data items.',
        },
        {
            type: 'tabs',
            key: 'tabs',
            components: [
                {
                    label: 'Display',
                    key: 'display',
                    weight: 0,
                    components: [
                        LABEL,
                        KEY,
                        HIDDEN,
                        CUSTOM_CSS_CLASS
                    ]
                },
                ADVANCED,
            ]
        }
    ]
};

class ContentField extends FormioContentField {
    static editForm() {
        return CONTENT_EDIT_TABS;
    }
}

export default ContentField;
