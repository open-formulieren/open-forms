/**
 * A form widget to select family members.
 */
import {Formio} from 'formiojs';
import {DEFAULT_CHOICES_TABS} from "./edit/tabs";

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
        };
    }

    get defaultSchema() {
        return NpFamilyMembers.schema();
    }

    static editForm() {
        return {components: [DEFAULT_CHOICES_TABS]};
    }
}

export default NpFamilyMembers;
