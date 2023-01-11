import {Formio} from 'formiojs';

const DatamapFormio = Formio.Components.components.datamap;

class Datamap extends DatamapFormio {
  static schema(...extend) {
    return DatamapFormio.schema(
      {
        disableKey: false,
      },
      ...extend
    );
  }

  get keySchema() {
    return {
      type: 'textfield',
      input: true,
      hideLabel: true,
      label: this.component.keyLabel || 'Key',
      key: '__key',
      disableBuilderActions: true,
      disabled: this.component.disableKey,
    };
  }
}

export default Datamap;
