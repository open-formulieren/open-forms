/**
 * A form widget to select family members.
 */
import {Formio} from 'formiojs';

import {
  CLEAR_ON_HIDE,
  DESCRIPTION,
  HIDDEN,
  IS_SENSITIVE_DATA,
  KEY,
  LABEL_REQUIRED,
  MULTIPLE,
  PRESENTATION,
  TOOLTIP,
} from './edit/options';
import {ADVANCED, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
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

  static editForm() {
    // The datagrid that would usually be shown to set the values of the checkboxes is not present, since the
    // values will be set by the backend
    let BASIC_TAB = {
      key: 'basic',
      label: 'Basic',
      components: [
        {
          type: 'htmlelement',
          tag: 'div',
          content: 'Note that any family member without a BSN will not be displayed.',
        },
        LABEL_REQUIRED,
        KEY,
        DESCRIPTION,
        TOOLTIP,
        PRESENTATION,
        MULTIPLE,
        HIDDEN,
        CLEAR_ON_HIDE,
        {...IS_SENSITIVE_DATA, defaultValue: true},
        {
          type: 'checkbox',
          key: 'includePartners',
          label: 'Include partners',
          tooltip: 'Whether to add partners information to the component.',
          defaultValue: true,
        },
        {
          type: 'checkbox',
          key: 'includeChildren',
          label: 'Include children',
          tooltip: 'Whether to add children information to the component.',
          defaultValue: true,
        },
      ],
    };

    const sensitiveBasicTabs = {
      type: 'tabs',
      key: 'tabs',
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [sensitiveBasicTabs]};
  }
}

export default NpFamilyMembers;
