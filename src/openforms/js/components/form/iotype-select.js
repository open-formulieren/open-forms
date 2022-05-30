import SelectField from './select';

class InformatieObjectTypeSelectField extends SelectField {
  setItems(items, fromSearch) {
    const groups = {};
    for (const item of items) {
      const choice = {
        value: item.informatieobjecttype.url,
        label: item.informatieobjecttype.omschrijving,
      };
      if (!(item.catalogus.domein in groups)) {
        groups[item.catalogus.domein] = [];
      }
      groups[item.catalogus.domein].push(choice);
    }

    const choices = [];
    for (const [index, groupName] of Object.keys(groups).entries()) {
      const entry = {
        label: groupName,
        id: index + 1,
        disable: false,
        choices: groups[groupName],
      };
      choices.push(entry);
    }

    this.choices.setChoices(choices, 'value', 'label', true);

    this.isScrollLoading = false;
    this.loading = false;

    const searching = fromSearch && this.choices?.input?.isFocussed;

    if (!searching) {
      // If a value is provided, then select it.
      if (!this.isEmpty()) {
        this.setValue(this.dataValue, {
          noUpdateEvent: true,
        });
      } else if (this.shouldAddDefaultValue && !this.options.readOnly) {
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

export default InformatieObjectTypeSelectField;
