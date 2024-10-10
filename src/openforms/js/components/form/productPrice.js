/**
 * A form widget to select product prices.
 */
import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';
import {get} from '../../utils/fetch';
import {PRODUCT_PRICES_ENDPOINT} from '../admin/form_design/constants'; // TODO add new endpoint or add price options to existing one.

export const getProducts = async () => {
  const response = await get(PRODUCT_PRICES_ENDPOINT);
  return response.data.map(item => ({
    label: item.name,
    value: item.uuid,
  }));
};

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
