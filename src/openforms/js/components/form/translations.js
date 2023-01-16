import {Formio} from 'react-formio';

import {DEFAULT_TEXT_TABS} from './edit/tabs';

class TranslationsDataGrid extends Formio.Components.components.datagrid {
  static editForm() {
    return {components: [DEFAULT_TEXT_TABS]};
  }

  hasRemoveButtons() {
    return false;
  }

  get canAddColumn() {
    return false;
  }

  hasBottomSubmit() {
    return false;
  }

  getRows() {
    let rows = this.rows.map(row => {
      const components = {};
      _.each(row, (col, key) => {
        components[key] = col.render();
      });
      return components;
    });
    console.log(rows);
    return rows;
  }
}

export default TranslationsDataGrid;
