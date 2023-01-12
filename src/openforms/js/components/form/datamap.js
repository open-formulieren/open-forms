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

  setRowComponentsData(rowIndex, rowData) {
    _.each(this.rows[rowIndex], component => {
      // Fix to prevent keys not matching the data
      if (component.key === '__key' && !!component.data.__key) {
        return;
      }

      if (component.key === '__key') {
        component.data = {
          __key: Object.keys(rowData)[rowIndex],
        };
      } else {
        component.data = rowData;
      }
    });
  }
}

export default Datamap;
