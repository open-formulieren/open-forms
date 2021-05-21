/**
 * A form widget to select family members.
 */
import {Formio} from 'formiojs';
import {defineEditFormTabs} from './abstract';

const SelectBoxes = Formio.Components.components.selectboxes;

class NpFamilyMembers extends SelectBoxes {
    static schema(...extend) {
        return SelectBoxes.schema({
            label: 'Selecteer gezinsleden',
            key: 'npFamilyMembers',
            type: 'npFamilyMembers',
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
                    {
                        type: 'checkbox',
                        key: 'showInEmail',
                        label: 'Show in email',
                        tooltip: 'Whether to show this value in the confirmation email'
                    },
                ]
            }
        ]
    }
]);

Formio.registerComponent('npFamilyMembers', NpFamilyMembers);
