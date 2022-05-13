import {Formio} from 'formiojs';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from './edit/tabs';

const Select = Formio.Components.components.select;

const values = [
  {
    type: 'datagrid',
    input: true,
    label: 'Values',
    key: 'data.values',
    tooltip:
      'The radio button values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
    weight: 10,
    reorder: true,
    defaultValue: [{label: '', value: ''}],
    components: [
      {
        label: 'Label',
        key: 'label',
        input: true,
        type: 'textfield',
      },
      {
        label: 'Value',
        key: 'value',
        input: true,
        type: 'textfield',
        allowCalculateOverride: true,
        calculateValue: {_camelCase: [{var: 'row.label'}]},
      },
    ],
  },
];

class SelectField extends Select {
  static editForm() {
    const BASIC_TAB = {
      ...BASIC,
      components: [...BASIC.components, ...values],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION],
    };
    return {components: [TABS]};
  }
}


class InformatieObjectTypeSelectField extends SelectField {
    setItems(items, fromSearch) {
        let groups = {}
        for(let item of items) {
            let choice = {value: item.url, label: item.description}
            if(!(item.catalogusDomain in groups)) {
                groups[item.catalogusDomain] = []
            }
            groups[item.catalogusDomain].push(choice)
        }

        let choices = []
        for (let [index, groupName] of Object.keys(groups).entries()) {
            let entry = {
                label: groupName,
                id: index+1,
                disable: false,
                choices: groups[groupName],
            }
            choices.push(entry)
        }

        this.choices.setChoices(choices, 'value', 'label', true);

        this.isScrollLoading = false;
        this.loading = false;

        const searching = fromSearch && this.choices?.input?.isFocussed;

        if (!searching) {
        // If a value is provided, then select it.
        if (!this.isEmpty()) {
            this.setValue(this.dataValue, {
            noUpdateEvent: true
            });
        }
        else if (this.shouldAddDefaultValue && !this.options.readOnly) {
            // If a default value is provided then select it.
            const defaultValue = this.defaultValue;
            if (!this.isEmpty(defaultValue)) {
            this.setValue(defaultValue);
            }
        }
        }

        // Say we are done loading the items.
        this.itemsLoadedResolve();
    }
}


export default SelectField;
export {InformatieObjectTypeSelectField};
