/**
 * A form widget to select family members.
 */
import {Formio} from 'formiojs';
import {defineEditFormTabs, defineInputInfo} from './abstract';

const FieldComponent = Formio.Components.components.field;
// const FieldComponent = Formio.Components.components.textfield;

class NpFamilyMembers extends FieldComponent {
    static schema(...extend) {
        return FieldComponent.schema({
            label: 'Selecteer gezinsleden',
            key: 'npFamilyMembers',
            type: 'npFamilyMembers',
            mask: false,
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Gezinsleden',
            icon: 'fa fa-users',
            group: 'basic',
            weight: 10,
            schema: NpFamilyMembers.schema(),
        }
    }

    get defaultSchema() {
        return NpFamilyMembers.schema();
    }

    render() {
        return super.render(`
            <div ref="element">${getTemplate()}</div>
        `);
    }

    // get emptyValue() {
    //     return [];
    // }
}


defineEditFormTabs(NpFamilyMembers, [
    {
        type: 'tabs',
        key: 'tabs',
        components: [
            {
                key: 'basic',
                'label': 'Basic',
                components: [
                    {'type': 'textfield', key: 'label', label: 'Label'},
                ]
            }
        ]
    }
]);

Formio.registerComponent('npFamilyMembers', NpFamilyMembers);

export const getTemplate = () => {
    return "(Familieleden)";
};
