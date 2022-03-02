import {Formio} from 'formiojs';

const FormioFieldSet = Formio.Components.components.fieldset;

const FIELDSET_BASIC = {
    key: 'display',
    label: 'Display',
    components: [
        {
            type: 'textfield',
            key: 'label',
            label: 'Label'
        },
        {
            type: 'textfield',
            key: 'key',
            label: 'Property Name'
        },
        {
            type: 'checkbox',
            key: 'hidden',
            label: 'Hidden',
            tooltip: 'A hidden field is still a part of the form, but is hidden from view.'
        },
        {
            type: 'checkbox',
            key: 'clearOnHide',
            label: 'Clear on hide',
            tooltip: 'Remove the value of this field from the submission if it is hidden',
        },
        {
            type: 'checkbox',
            key: 'hideHeader',
            label: 'Hide fieldset header',
            tooltip: 'Hide the line and the label above the fieldset in the form',
            defaultValue: false,
        }
    ]
};

class FieldSet extends FormioFieldSet {

    static editForm(...extend) {
        const parentEditForm = FormioFieldSet.editForm();
        parentEditForm.components[0].components = [
            FIELDSET_BASIC,
            // The 'API' tab is removed, since the only useful attribute it contained was the 'key', but we
            // have this field in the FIELDSET_BASIC tab.
            // The Conditions and Layout tabs have also been removed since they are not used
            parentEditForm.components[0].components[3], // Logic tab
        ];
        return parentEditForm;
    }
}

export default FieldSet;
