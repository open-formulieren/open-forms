/**
 * A form widget to select family members.
 */
import {Formio} from 'formiojs';
import {
    ADVANCED,
    REGISTRATION,
    SENSITIVE_BASIC,
    VALIDATION
} from './edit/tabs';

const SelectBoxes = Formio.Components.components.selectboxes;

class NpFamilyMembers extends SelectBoxes {
    static schema(...extend) {
        return SelectBoxes.schema({
            label: 'Select family members',
            key: 'npFamilyMembers',
            type: 'npFamilyMembers',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Family members',
            icon: 'users',
            group: 'basic',
            weight: 10,
            schema: NpFamilyMembers.schema(),
        };
    }

    get defaultSchema() {
        return NpFamilyMembers.schema();
    }

    static editForm() {
        // The datagrid that would usually be shown to set the values of the checkboxes is not present, since the
        // values will be set by the fill_out_family_members function in openforms/contrib/brp/field_types.py
        let basicFieldsNoDefault = {...SENSITIVE_BASIC};
        basicFieldsNoDefault.components = basicFieldsNoDefault.components.filter(component => component.key !== 'defaultValue');
        const sensitiveBasicTabs = {
            type: 'tabs',
            key: 'tabs',
            components: [
                basicFieldsNoDefault,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
            ]
        };
        return {components: [sensitiveBasicTabs]};
    }
}

export default NpFamilyMembers;
