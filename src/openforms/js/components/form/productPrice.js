/**
 * A form widget to select product prices.
 */
import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const Radio = Formio.Components.components.radio;

class ProductPrice extends Radio {
  static schema(...extend) {
    const schema = Radio.schema(
      {
        label: 'Select a product',
        key: 'productPrice',
        type: 'productPrice',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Product Price',
      icon: 'file',
      group: 'basic',
      weight: 10,
      schema: ProductPrice.schema(),
    };
  }

  get defaultSchema() {
    return ProductPrice.schema();
  }
}

export default ProductPrice;