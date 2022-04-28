import {Formio} from 'formiojs';
import {HIDDEN, KEY, LABEL} from './edit/options';
import {ADVANCED} from './edit/tabs';

const FormioContentField = Formio.Components.components.content;

const CUSTOM_CSS_CLASS = {
    weight: 500,
    type: 'select',
    input: true,
    label: 'Custom CSS Class',
    key: 'customClass',
    data: {
        values: [
            {label: 'Warning', value: 'warning'},
            {label: 'Info', value: 'info'},
            {label: 'Error', value: 'error'},
            {label: 'Success', value: 'success'},
        ],
    },
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
