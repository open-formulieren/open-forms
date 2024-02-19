/**
 * A form widget to select family members.
 */
import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const SelectBoxes = Formio.Components.components.selectboxes;

class NpFamilyMembers extends SelectBoxes {
  static schema(...extend) {
    const schema = SelectBoxes.schema(
      {
        label: 'Select family members',
        key: 'npFamilyMembers',
        type: 'npFamilyMembers',
        includePartners: true,
        includeChildren: true,
      },
      ...extend
    );
    return localiseSchema(schema);
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
}

export default NpFamilyMembers;
